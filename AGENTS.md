# AGENTS.md — operating contract for all coding/research agents

**Read this before modifying files or running any experiment.** Applies to Codex, Claude Code, Copilot, OpenAI agents, people, scripts and orchestrators.

## Identity and hard boundaries
- This is an **independent experimental repository**, NOT BIXML, Xim, Revit or the normative public schema registry. **Do not modify, fork internals from, or sync to those projects** unless the owner separately authorizes a specific integration.
- The tested hypothesis is: **LLM edits declarative XML source files directly.** The agent under test MUST NOT call a BIM command bus, typed authoring API, geometry function, IfcOpenShell mutator, or Python editing helper to implement the *direct-markup* arm. Only the trusted *runtime outside the LLM loop* may translate edited XML into IFC. For the imperative baseline, LLM-generated Python/IfcOpenShell is expected.
- Document any unavoidable loss of fidelity when the XML is an IFC-backed partial view; do not call it lossless, self-contained native BIM or final BIXML unless evidence establishes that claim.
- A GitHub Issue is a specification, **not proof of implementation**. Do not state that runs, benchmarks, evaluators or support exist until independently verified.

## Agent scope and concurrency
1. Start with this file, README, docs/RESEARCH_PROTOCOL.md, docs/ARCHITECTURE.md, docs/BENCHMARK_CATALOG.md and your assigned Issue.
2. One agent/PR = one issue or a pre-approved coherent set; use `feat/<issue>-<scope>`. No direct pushes to main, force pushes, rebases of other people's work, or branch resets.
3. Path ownership per issue: dataset adapter (`src/data/`), runtime (`src/runtime/`), direct XML (`src/direct_markup/`), imperative (`src/imperative_control/`), evaluator (`src/evaluation/`), experiment runner (`experiments/`), scientific protocol (`docs/`), tests (`tests/`). Cross-boundary edits need an issue discussion and explicit owner acknowledgement. Review shared manifests before editing concurrently.
4. Published/preregistered datasets, scoring formulas, sample lists, hidden-GT barrier and prompt budgets **must not be changed to improve observed scores**. Any post-hoc changes must be separately versioned and disclosed.
5. Do not run simultaneous agents against the same model/output directory; each trial gets an immutable input, isolated sandbox and own artifact prefix. No reuse of edited models between arms.

## Source/answer separation and fair controls
- Only public input IFC, instructions, model schema and the arm-specific allowed environment are visible to the LLM; keep ground-truth IFC, target GUIDs used for grading, private evaluation scripts, reference solutions and held-out answers outside the agent's filesystem and prompts.
- Exclude answer leakage via logs, serialized tool outputs, directory listings, environment variables, training examples and model caches. Benchmark metadata fields can contain answer hints: sanitize the agent payload.
- Match task inputs, test model ID, decoding settings, retry limits, timeouts, tool-call budgets, number of samples, hardware and backend versions where feasible. Record differences.
- The public benchmark evaluator may be missing or incomplete; never fabricate a numerical comparison. Identify metric origin as `official`, `independent-reimplementation` or `surrogate`.
- Track engine unsupported and invalid edits separately from LLM instruction failures. Never silently skip a failed test.

## Security, cost and licensing
- No API tokens, login material, large IFC corpora or personal data in git or issue bodies. Use environment variables/secret managers, not committed .env files.
- No mass benchmarks, paid inference, expensive geometry/regeneration or dataset downloads without explicit budget, model and storage authorization. Small non-billed local validation may run within scope.
- Public benchmark tasks, IFC models, results and model-generated text have **different rights**. Check per-model license and redistributability before copying. Default: store datasets outside Git and identify by checksum.
- No unexpected changes to host services, databases, remote machines, Xim worktrees, local PowerPoint/Word installations or GitHub Pages.

## Acceptance evidence for each PR
- Issue link, before/after exact behavior, test command and stdout summary, offline reproduction instructions, all modified files, commit SHA, data/model hashes when applicable.
- At least one positive and one negative/failure fixture for parsers/validators; deterministic fixture for IFC mutations; no known silent data loss.
- Clearly separate verified observations, engineering assumptions and untested claims.
- If blocked, report exact dependency and evidence; do not invent a passing result.

## The core non-negotiable
**XML is what the LLM edits.** APIs, translators and compiled geometry may exist behind the runtime boundary, but they cannot be the direct-markup arm's LLM authoring interface. The metric and ground truth remain independent of either arm.

**한국어:** 이 저장소는 독립적인 실험 전용입니다. LLM의 선언적 마크업 직접 편집 원칙, 대조군의 공정성, 정답 IFC 비공개, 버전 고정, Agent 작업경로 격리, 비용·보안·라이선스 검증을 준수합니다. 기존 Xim/BIXML 저장소는 수정하지 않습니다.
