# BIM Markup Bench

**Independent, reproducible research playground for LLM-native BIM authoring.**

> **Research question:** Does directly editing a *declarative, human-readable BIM source file* improve LLM building-model editing compared with writing imperative Python/IfcOpenShell code, under matched capabilities and evaluation conditions?

This is deliberately **not** the BIXML language specification, not Xim, not a Revit clone, and not an API-based BIM agent project. A *toy experimental XML dialect* will be designed only for this repository; it is not the final BIXML syntax or a published namespace.

**Status: planning / GitHub Issues only.** No runtime, benchmark scorer, model integration, experiment runs, accuracy numbers, or reproducibility results are implemented or claimed yet.

## Experimental arms

| Arm | Agent's authoring surface | Runtime/backend | Main claim tested |
| --- | --- | --- | --- |
| **D: direct-declarative** (proposed) | LLM opens and edits a version-controlled `building.xml` file **directly** | XML semantic compiler -> IFC mutation/export | Markup as authoring language; **no BIM API/CommandBus in the LLM loop** |
| **I: imperative-control** | LLM writes Python source invoking IfcOpenShell | IfcOpenShell -> IFC mutation/export | Conventional code/API driven authoring |
| **D0: deterministic-direct-oracle** (non-LLM ceiling) | Known-correct hand-authored XML patch | Same declarative compiler -> IFC export | Determines what the *runtime* can accomplish without LLM failure |
| **P0: deterministic-Python-oracle** (non-LLM ceiling) | Known-correct Python edit | Same IFC backend | Determines whether both arms can represent and execute the same task |

For the *matched-backend comparison*, both arms should use the **same IfcOpenShell version, geometry kernel, input IFC, isolated task environment and independent scorer**. The declarative arm may rely on IfcOpenShell **inside the runtime**, but must not expose its mutation API to the LLM. A direct full-file declarative authoring arm is a later extension and should not be confused with the initial IFC-preserving overlay technique.

## External benchmarks (verification gates first)

1. **BIM-Edit** — primary editing benchmark: [tasks, 324 rows](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks); [IFC input/ground-truth assets](https://huggingface.co/datasets/BIM-Edit/BIM-Edit); [paper](https://arxiv.org/abs/2606.20146). Operations create/update/delete; categories direct/spatial/topological; six element classes. The benchmark input and expected output files must be aligned, hashed and frozen before use.
2. **BIBIMBAP** — [EC3 paper](https://ec-3.org/publication/ec32026_271/): 100 curated CRUD tasks, including Read, with expected outputs and task-level test scripts described by the authors. **Availability/licensing of usable machine-readable artifacts and official evaluator are an unresolved acquisition gate.** Do not claim a public runnable test suite until obtained.
3. **IFC-Bench v2** — [dataset](https://huggingface.co/datasets/sylvainHellin/ifc-bench): 1,027 information-retrieval Q&A pairs, spanning 37 IFC models in the associated 2026 paper (dataset revisions may change model inventories). This is **READ-only** and must be reported as a separate task family, not mixed into edit success percentages.

## Scientific guardrails

- The *benchmark ground-truth IFC, task target annotations, evaluator internals and hidden answers* are never exposed to the tested LLM. Score only after generation.
- Pre-register task inclusion, element/category/scene coverage, model version and prompt budgets; report **all attempted tasks**, failures and unsupported tasks, not only passing cases.
- Report **full-set intention-to-treat success** and separately **common-supported-subset success**; avoid giving either arm an unfair scope advantage.
- Keep semantic/topological relation edits first-class; moving a shape without preserving its wall/space/host relationships does **not** count as successful BIM editing.
- Before any LLM experiment, measure input IFC -> runtime -> unchanged IFC round-trip preservation and deterministic ceiling on exact tasks. This prevents assigning backend faults to the language.
- Compare paired task outcomes; log per-task errors, cost, latency, tool turns, token usage, semantic damage to untouched objects, and geometry/semantic/topology subscores.
- No unaudited evaluator: if official scoring scripts cannot be obtained, label any reconstruction **independent approximation**, verify it on fixtures and do not imply numeric comparability to published scores.
- Use snapshot/commit + SHA-256 for datasets, library versions, prompts, model IDs, evaluator and source tree. Respect each IFC model's individual license.
- Never run paid LLM evaluations, bulk downloads or high-cost geometry jobs without budget authorization.

## Planned repository layout

```text
bim-markup-bench/
├── AGENTS.md                      # REQUIRED agent safety and ownership policy
├── docs/
│   ├── RESEARCH_PROTOCOL.md       # hypotheses, metrics, fairness, reporting
│   ├── ARCHITECTURE.md            # experiment-only XML & IFC backend boundaries
│   ├── BENCHMARK_CATALOG.md       # datasets, licensing, version pinning
│   └── ROADMAP.md                 # gates and GitHub Issue tracker
├── src/
│   ├── direct_markup/             # proposed, not yet implemented
│   ├── imperative_control/        # proposed, not yet implemented
│   ├── runtime/                   # proposed, not yet implemented
│   └── evaluation/                # proposed, not yet implemented
├── experiments/                   # proposed, not yet implemented
├── tests/                         # proposed, not yet implemented
└── results/                       # local results, NOT benchmark data or secrets
```

## Where to begin

See [the epic and all issues](https://github.com/pikaybh/bim-markup-bench/issues), [Agent operating rules](AGENTS.md), [Research protocol](docs/RESEARCH_PROTOCOL.md), [Architecture boundary](docs/ARCHITECTURE.md) and [the roadmap](docs/ROADMAP.md). Work is staged: **data/evaluator audit -> IFC preservation -> XML & deterministic oracle -> matched pilot -> full benchmark -> secondary tests**.

## Independence and security

No code copy or Git submodule from Xim/BIXML, no changes to those repositories, no changes to production or cloud servers, and no shared deployment. Public benchmark licenses do not automatically permit redistributing every IFC model; large datasets, reference IFC outputs and results belong in separately permissioned, ignored local storage. Never commit API keys or sensitive prompts.

**Licensing:** This experimental repository has not yet selected its own code license. Do not infer a grant of reuse from its public visibility.

**한국어 요약:** 이 저장소는 BIXML/Xim을 수정하지 않고, LLM의 **XML 원본 직접 편집**과 **Python/IfcOpenShell 코드 생성**을 동일한 IFC 백엔드 및 독립 평가기로 비교하기 위한 토이 연구입니다. 현재는 실행 코드가 아닌 계획·이슈 단계입니다.

## Development environment (G0 #7)

See [Environment](docs/ENVIRONMENT.md) and [Compute / API budget](docs/COMPUTE_BUDGET.md).
For Mac ARM64, Python 3.12 and uv 0.8.5:
1. uv python install 3.12
2. uv sync --frozen --python 3.12
3. .venv/bin/python tools/doctor.py
4. .venv/bin/python -m unittest discover -s tests -v
5. .venv/bin/python tools/cost_budget.py

These are offline-only checks, not a functioning benchmark or model runner. API calls remain blocked and the .env.example template contains no secrets.

## IFC read projection (experimental G1 #11)

Read an existing supported IFC4X3 input without modifying it:

    .venv/bin/python -m tools.project_ifc tests/fixtures/synthetic/input.ifc \
      --xml-out data/projections/building.xml
    .venv/bin/python -m tools.validate_markup data/projections/building.xml

The XML is an editable **managed projection**, not a complete source-free BIM
document; unsupported types, especially missing IfcSpace geometry, remain
opaque in the immutable original IFC. [Coverage and limitations](reports/ifc_projection_coverage.md).
A safe byte-identical IFC copy can be made with --noop-copy, but actual edits
remain blocked until #12/#13 deliver the typed semantic compiler.

## Trusted declarative IFC mutation compiler (G1 #13: narrow slice)

An experimental wall-only compiler can now apply **actual IFC geometry changes**
to a new output file without exposing authoring APIs to the LLM:

    .venv/bin/python -m tools.project_ifc tests/fixtures/synthetic/input.ifc --xml-out data/projections/demo.xml
    # Edit the declarative wall height attribute in data/projections/demo.xml
    .venv/bin/python -m tools.compile_markup --source-ifc tests/fixtures/synthetic/input.ifc --edited-xml data/projections/demo.xml --result-ifc data/projections/result.ifc

Current accepted edits: standalone straight Wall create/delete and existing
Wall swept-solid height change only. All others fail closed. See
[compiler coverage and safety](docs/compilation/wall_compiler_v0.md).
This is not yet full BIM-Edit (324 tasks) or standalone native BIXML.

## G1 deterministic source markup vs imperative reference (Issue #16)

Before spending on LLM evaluation, the independent, offline synthetic D0
(XML) and I0 (Python/IfcOpenShell) oracles must agree on six create/update/
delete, hosted placement and topological relation scenarios:

    .venv/bin/python -m tools.verify_g1_oracles
    .venv/bin/python -m tools.g1_release_gate --enforce

The first command tests own small IFC-only fixtures and produces
reports/deterministic_ceiling.json with PASS_SYNTHETIC_ONLY. The second
**intentionally fails**: there are no official BIM-Edit 324-task scores and
the required IFC asset verification, independent scorer, full class engine,
and matched arm gates are still incomplete. See docs/gates/G1_evidence.md.

## G2 source-only file authoring stub (Issue #17, offline)

A no-LLM adapter applies a tiny textual edit to building.xml, records an
audited unified diff and gives the accepted source to a separate trusted
IFC compiler. No BIM authoring API is exposed in the authoring interface.

    .venv/bin/python -m unittest tests.test_source_only_agent -v
    .venv/bin/python -m tools.source_only_stub_demo --output-ifc data/offline_stub_result.ifc

This demonstration is not a real LLM trial, sandbox or official score.
See docs/g2/source_only_harness.md and the still-BLOCKED G1 release gate.

## G2 imperative Python control (Issue #18, preflight only)

The imperative baseline has an input-parity and Python source submission
adapter. Proposed solution.py text is syntax-checked and audited but
**never executed** until OS/container isolation is implemented (#19).

    .venv/bin/python -m tools.imperative_preflight_demo
    .venv/bin/python -m unittest tests.test_imperative_control -v

This is not a paid model experiment or benchmark result. See
docs/g2/imperative_baseline.md and the still-blocked G1 release gate.

## G2 file staging and withheld process execution (#19, partial)

Each task and arm now gets a distinct reproducible staging directory with
separate model-input, trusted compiler and grader paths. File integrity and
source visibility tests pass, but host OS isolation is not certified, so
untrusted Python and paid experiments remain disabled. See
docs/SECURITY_ISOLATION.md.

## G2 offline paired trial scheduler (#20, partial)

The local CLI has doctor, validate-data, run, score and report commands.
Only **nonbilling mock scheduling** is implemented. A fixed
2-task × 2-arm × 2-seed demo creates eight immutable manifests and
verifies deterministic pairing, context parity, budgets and resume.
No real model calls, Python execution or official scores occur.

    .venv/bin/python -m src.runner.cli doctor
    .venv/bin/python -m src.runner.cli run --offline-mock \
      --output-root /tmp/bim-g2-offline-demo
    .venv/bin/python -m src.runner.cli report \
      --output-root /tmp/bim-g2-offline-demo

Score and doctor --enforce block until isolation and independent official
scoring are verified. See docs/g2/offline_runner.md.

## G2 independent IFC-native scorer (#21, partial)

An arm-blind, grader-only component now compares native IFC target geometry,
product properties/materials, typed spatial/topological relationships and
unexpected collateral edits. Metric provenance is always independent,
NEVER official BIM-Edit equivalence.

    .venv/bin/python -m unittest tests.test_bim_edit_scorer -v
    .venv/bin/python -m tools.score_independent_ifc

See docs/g2/independent_scorer.md. The main benchmark scoring and paid
model gates remain disabled pending official corpus/capability calibration.

## G2 independent scorer calibration and blocked release (#22)

The own synthetic calibration suite checks 17 fixed positive/negative
geometry, IFC semantic and native topology conditions, plus translation/
rotation sensitivity and strict score-model arm blindness. A 108-strata
capability matrix accounts for all 324 public metadata task rows without
claiming official scores.

    .venv/bin/python -m tools.calibrate_g2
    .venv/bin/python -m tools.calibrate_g2 --enforce

The latter must exit 2; live model/provider and generated Python execution
remain blocked. See reports/evaluator_calibration.md and
docs/gates/G2_evidence.md for limitations.

## G3 metadata-only 36-task pilot candidate (#23, partial)

A deterministic candidate sampler fixes two public task IDs in each
of 18 operation × instruction × scene cells (36 unique tasks). Its
methodological protocol and proposed budgets are DRAFT, not frozen:
no provider/model/version/price has been approved and no original
official IFC/GT content or OS sandbox has passed release gating.

    .venv/bin/python tools/prepare_pilot_candidate.py
    .venv/bin/python -m tools.pilot_preflight

The preflight intentionally exits 2 even when candidate ID/metadata
integrity is correct. It does not read API credentials or call a
model. See docs/protocol/pilot_preregistration_v1.md and
docs/PILOT_36_PREFLIGHT.md. Do not treat this as a scored study.

## G2 Docker kernel isolation measured (Issue #19, further partial)

A trusted, fixed synthetic Docker probe now verifies 15 launch/mount/env
constraints from Docker inspect BEFORE start, then 15 actual Linux
UID/cap/seccomp/cgroup/read-only/network/GT-key-denial conditions from
inside the container. It uses only an explicitly chosen, cached sha256
Linux image, never a mutable tag, private input or generated agent code.

    .venv/bin/python -m unittest tests.security.test_docker_isolation -v

The production Python/IfcOpenShell worker, full native IFC tests and paid
LLM gateway are NOT approved. The enforced live gate remains blocked; see
docs/SECURITY_ISOLATION.md for evidence, limitations and repeat procedure.
