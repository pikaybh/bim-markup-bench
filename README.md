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
