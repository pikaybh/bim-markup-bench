# G2 #17 direct XML file-only authoring harness — partial implementation

**Current state: LLM-free file-edit harness works end-to-end; real model,
physical OS sandbox and multi-task scored pilot are NOT ready.**

The only intended authoring surface is the original declarative building.xml
file, analogous to an LLM editing HTML/JS, not a BIM authoring CommandBus.
The trusted internal IFC4X3 compiler can use IfcOpenShell, but the model
tool interface has no IFC mutation function, Python execution endpoint,
network calls, shell commands or access to hidden benchmark ground truth.

## Observable context and modes

The experiment workspace contains building.xml, language_spec.md and a
read-only input.ifc copy of the immutable synthetic test file. The model-
visible context is instruction, task ID, file name, XML source, source byte
SHA-256, toy language specification and a file-text-edit allowlist only.

The model does not receive the original source file path, raw target annotation,
a hidden GT IFC, evaluator code, cost/billing keys or backend compiler tools.
The actual source IFC is used by the trusted controller independently of the
model's patch proposal.

Predeclared mode is either one_shot (exactly one attempt, no diagnostics fed
back) or feedback (up to five attempts with sanitized parser diagnostics).
Neither silently changes feedback policy or token budgets. Actual LLM
token consumption is null because no model provider has been invoked.
A per-task max wall seconds and maximum edited XML bytes is enforced by the
file adapter, but this is NOT a sufficient external provider time or memory
limit for future production runs.

Only two file-level edit types are supported: surgical text substitution
(unique exact anchor) and validated whole-file XML rewrite. The former
preserves all unrelated XML comments, order and stable local IDs. All edits
require a current source byte SHA-256; stale/duplicate anchors, malformed
XML, changed source IFC digest or excess byte size fail without replacing
the last valid building.xml.

For every attempt, a machine-readable trace records the exact filename,
source version, textual unified diff, mode, attempt number, measured elapsed
time, rejection status, read/edit operations and successful BIM authoring API
calls (zero). This is an authoring-file audit trace, NOT a native IFC
benchmark score.

## Trust boundary, not imaginary security

In the LLM-free unit test, an innocuous stub produces the file-text patch.
The trusted owner invokes TrustedCompilationController only after the
adapter has accepted valid declarative XML. This invocation is not exposed
to the stub and never appears as a model-authoring tool. The compiler then
reparses, binds and writes a separate, new IFC result.

This is a **logical interface separation** in the same Python process.
It is NOT sufficient OS isolation against malicious generated Python.
The imperative arm must not execute arbitrary untrusted Python before
G2 #19 installs actual container/VM filesystem, network, process and resource
isolation. Physical OS limits and actor-specific execution traces must
be verified before any paid LLM test.

## Local reproduction (no API/network/paid models)

    uv sync --frozen --python 3.12
    .venv/bin/python -m unittest tests.test_source_only_agent -v
    .venv/bin/python -m tools.source_only_stub_demo --output-ifc data/offline_stub_result.ifc

The second command writes a NEW result IFC only and prints a file-tool trace
summary; output is under gitignored data/. Reusing the same result filename
is rejected (no accidental overwrite). The synthetic source's wall height
changes from 3.0 to 3.3m physically, while native void/fill relationships
survive. No GT, official task or LLM provider is used.

## Remaining acceptance gates

- Adapter for actual chosen LLM provider and audited actual token/time use.
- Robust container/VM sandbox and capability separation (#19), independent
  same-budget retries and logging (#20).
- Equal effective task context and real source geometry inspection API parity
  for the Python control arm (#18), preregistered ablation of full XML
  versus concise projection.
- Official whole task dataset, evaluator, geometry and topology support
  (#3/#4/#12–#16/#21/#22).
- Explicit renewed paid budget approval. Current G1 release gate is BLOCKED.

This is an isolated toy study; no production BIMXL/BIXML/Xim changes.
