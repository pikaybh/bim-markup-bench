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

## Executable GitHub Issue index (created 2026-11-06)

The [master epic #1](https://github.com/pikaybh/bim-markup-bench/issues/1) tracks all gates. Each issue includes concrete file contracts, prerequisites, positive/negative tests, evidence requirements and out-of-scope constraints. Creating an issue is **not** completing it.

| Gate / milestone | GitHub Issues | Exit condition |
| --- | --- | --- |
| **G0** Foundations | [#2](https://github.com/pikaybh/bim-markup-bench/issues/2) protocol; [#3](https://github.com/pikaybh/bim-markup-bench/issues/3) BIM-Edit pinning; [#4](https://github.com/pikaybh/bim-markup-bench/issues/4) scorer audit; [#5](https://github.com/pikaybh/bim-markup-bench/issues/5) BIBIMBAP availability; [#6](https://github.com/pikaybh/bim-markup-bench/issues/6) IFC-Bench; [#7](https://github.com/pikaybh/bim-markup-bench/issues/7) environment; [#8](https://github.com/pikaybh/bim-markup-bench/issues/8) fixtures/GT separation | Data, scorer, versioning, rights and leakage evidence |
| **G1** Runtime | [#9](https://github.com/pikaybh/bim-markup-bench/issues/9) XML spec; [#10](https://github.com/pikaybh/bim-markup-bench/issues/10) parser; [#11](https://github.com/pikaybh/bim-markup-bench/issues/11) IFC projection; [#12](https://github.com/pikaybh/bim-markup-bench/issues/12) semantic graph; [#13](https://github.com/pikaybh/bim-markup-bench/issues/13) compiler; [#14](https://github.com/pikaybh/bim-markup-bench/issues/14) geometry; [#15](https://github.com/pikaybh/bim-markup-bench/issues/15) topology; [#16](https://github.com/pikaybh/bim-markup-bench/issues/16) deterministic oracle | Same task succeeds D0/I0; invalid edits fail closed |
| **G2** Matched comparison | [#17](https://github.com/pikaybh/bim-markup-bench/issues/17) direct XML LLM; [#18](https://github.com/pikaybh/bim-markup-bench/issues/18) Python control; [#19](https://github.com/pikaybh/bim-markup-bench/issues/19) sandbox; [#20](https://github.com/pikaybh/bim-markup-bench/issues/20) runner/budgets; [#21](https://github.com/pikaybh/bim-markup-bench/issues/21) evaluator; [#22](https://github.com/pikaybh/bim-markup-bench/issues/22) calibration | Blind independent scoring and equal tool/model access validated |
| **G3** Pilot | [#23](https://github.com/pikaybh/bim-markup-bench/issues/23) preregistration; [#24](https://github.com/pikaybh/bim-markup-bench/issues/24) pilot runs; [#25](https://github.com/pikaybh/bim-markup-bench/issues/25) statistical analysis | Predeclared paired pilot and complete failure report |
| **G4** BIM-Edit 324 | [#26](https://github.com/pikaybh/bim-markup-bench/issues/26) full sweep; [#27](https://github.com/pikaybh/bim-markup-bench/issues/27) final primary report | 324 tasks accounted for with ITT & supported denominator |
| **G5** Extensions and reporting | [#28](https://github.com/pikaybh/bim-markup-bench/issues/28) IFC-Bench QA; [#29](https://github.com/pikaybh/bim-markup-bench/issues/29) BIBIMBAP conditional; [#30](https://github.com/pikaybh/bim-markup-bench/issues/30) ablations; [#31](https://github.com/pikaybh/bim-markup-bench/issues/31) reproduction/paper | Rights-cleared secondary evaluation, reproducibility package |

### Suggested initial parallel assignment (does not assign GitHub users)

- Research/Data agents: #3, #4, #5, #6; coordinate #2 and shared task manifest changes.
- Runtime agents: start at #9 and #10, then #11 and #12; #13–#16 follow contracts.
- Infrastructure/Security agent: #7 and #8; #19 starts after the G0 threat model.
- Comparators/Scoring agents: #17–#22 **after G1 oracle release**, with separate paths to avoid overlap.

**No one is currently assigned.** Each subagent must read root AGENTS.md and claim a path-scoped Issue before writing. Specific owner assignment and paid compute approvals are separate decisions.
