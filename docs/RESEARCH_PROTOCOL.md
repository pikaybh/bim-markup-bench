# Pre-experimental Research Protocol (DRAFT — NOT preregistered)

**Status:** design draft; metrics and sample lists MUST be frozen as versioned preregistration before any evaluation. This draft is not a claim of executed experiments.

## Research question
For equal IFC input, output constraints, backend engine, LLM version and resource budgets, does directly editing a declarative, human-readable BIM source file improve the correctness, robustness, sample efficiency and cost of IFC model editing relative to imperative Python/IfcOpenShell code generation?

## Competing hypotheses (both directions allowed)
- **H1:** Direct markup increases per-task geometry/semantic/topology score or fully-correct pass rate on common-supported tasks.
- **H2:** Direct markup reduces invalid changes, incorrect references, regression to untouched objects and debugging/retry overhead.
- **H3:** Benefits vary by direct/spatial/topological instructions, by realistic/artificial scene, and by create/update/delete and IFC class.
- **Null or harm hypotheses:** XML conversion overhead, schema rigidity, incomplete IFC projection or longer model context make markup equal or worse than direct code. Negative results must be published.

## Conditions and causal isolation
- D = direct-markup LLM edits only `building.xml` (or split XML source files). It may read approved XML/schema docs and request compiler diagnostics; it may not invoke BIM modeling APIs. A separate trusted compiler applies source changes to a *clone* of the immutable input IFC.
- I = imperative LLM writes Python/IfcOpenShell code; the allowed Python interpreter runs in an isolated sandbox against a *clone* of the same immutable input.
- D0 and I0 deterministic non-LLM oracle scripts are mandatory **before** attempting scored LLM trials.
- Same backend IfcOpenShell version and geometric processing, where possible; identical LLM, model parameters, task prompt, max attempts, stop conditions, timeouts, quota and evaluation.
- Predefine whether tool access/feedback is (a) zero-feedback one-shot, or (b) matched number of compile/runtime feedback cycles. Report each setting separately. Do NOT allow direct arm a privileged precomputed model summary without matching information to control.

## Sampling and reporting
- Primary: BIM-Edit 324 tasks, 3 operations x 3 categories x 2 scene types; wall/slab/space/door/window/column. Task counts and pairing come from the pinned dataset manifest, never memory.
- Stage A: predeclared small (e.g. 18 or 36) stratified pilot, with fixed task IDs and a fixed seed BEFORE examining LLM outputs. Stratify by scene/operation/category and disclose element-class coverage. Do not select only easy passing tasks.
- Stage B: all 324 if execution and common capability gates pass. Report both **full-set ITT** (unsupported=fail) and **predeclared common-supported coverage**. Never hide unsupported cases.
- Separate IFC-Bench v2 QA evaluation (READ-only) from mutation results. BIBIMBAP CRUD evaluated under a separately pinned adaptation protocol once artifacts are legally available.

## Primary end points
1. Geometry score: official BIM-Edit metric when code/parameters available; otherwise a clearly named *independent approximation* with unit/pose/orientation and symmetry sanity checks.
2. Semantic score: entity class, attributes/property sets, spatial containment and preservation of unaffected IFC semantics.
3. Topological score: relationships such as `IfcRelContainedInSpatialStructure`, `IfcRelVoidsElement`, `IfcRelFillsElement`, `IfcRelSpaceBoundary`, `IfcRelConnectsElements` as relevant; no geometry-only success.
4. Fully-correct pass: all required per-task conditions within frozen tolerances. Report per-metric scores *and* strict pass rate; don't conceal catastrophic failures behind means.

## Secondary end points
- Token usage by role and total; API cost with price snapshot; wall time and CPU time; number of model or compiler invocations; retries; invalid XML, invalid IFC, parser errors, unsatisfied references, geometry failures.
- Preservation score for untouched GlobalIds, entity count, attributes, Psets, containment, material/type assignments and spatial relations.
- Runtime oracle ceilings (D0/I0) per task; coverage by category and known unsupported reasons.
- Number of prompt context tokens, schema/tool documentation size and input preprocessing time.

## Statistical analysis
- Pair tasks and random seeds across conditions, not unrelated sample sets. Compute paired deltas with bootstrap confidence intervals **clustered by input IFC/model** to account for correlated tasks; include exact CI method, seeds and alpha in frozen protocol.
- For binary fully-correct success, add paired contingency and (where appropriate) McNemar/exact test; for scores use paired bootstrap/model-level summaries.
- Multiple models / dataset families are secondary and must correct for multiple comparisons or be labeled exploratory. Report negative outcomes.
- No p-hacking: changes to parser, evaluator, threshold or inclusion after seeing results become a new protocol version and rerun.

## Leakage and artifact policy
- Ground-truth paths and target metadata are hidden from LLM process and prompt.
- Public input IFC accessible read-only through a copied task sandbox; reference IFC accessible **only** to evaluator process after predicted output finalized.
- Output file `result.ifc`, source diff, stdout/stderr, XML, generated Python, model messages, tool telemetry, token accounting, backend/compiler/evaluator versions and SHA-256 retained per trial.
- API keys remain in process environment and are **never** dumped in traces; redact other secrets and personal model data.

## Gates
G0 data/license/official evaluator inventory; G1 unchanged IFC preservation, D0/I0 oracle; G2 end-to-end XML authoring / Python control and blind scoring; G3 small matched pilot; G4 broader 324; G5 secondary benchmarks, ablations and paper.

**Important:** Each gate is unfulfilled until a linked Issue is closed with hard evidence.
