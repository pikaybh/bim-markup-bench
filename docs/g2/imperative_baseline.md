# G2 #18 — matched Python/IfcOpenShell code-generation control (preflight only)

**Partial implementation: model-visible submission envelope and static rejector,
NOT permission or capability to run generated Python.**

The Python baseline uses the same immutable input IFC SHA, original task ID
and natural-language instruction, XML projection and toy language specification
as the direct XML authoring arm from G2 #17. In addition, it receives reviewed
general IfcOpenShell API reference notes because its task is to generate
imperative Python program text rather than XML. This is a transparently
recorded arm-specific authoring reference; a matched observational capability
audit is still required before paid trials.

An agent proposal contains solution.py source text, a pinned original IFC SHA
and a declared success flag. The separate static preflight reader parses
source using ast.parse (no compile/exec/eval), restricts common import roots
to ifcopenshell/math/numpy, and rejects evident network/process/secret/GT
patterns. Every accepted candidate is kept in-memory and **cannot be executed**.
The trace records SHA, whether the candidate passed syntax preflight, attempt
count, elapsed wall time, no API runtime calls, and a hard flag that the OS
sandbox and model provider are absent. The trace schema records no output
files because nothing is run. A model success claim is never treated as a
benchmark score.

This static Python filter is deliberately labeled **UNTRUSTED / insufficient**.
It cannot enforce filesystem, process, network, system-call or memory
boundaries against adversarial Python; neither the filter nor ordinary Python
exceptions are a replacement for a real OS sandbox. Hence execution is
blocked unconditionally until G2 #19 provides a container/VM with:
- immutable/mounted input source, separate writable result path, GT omitted
- denied network/process escapes, restricted system resource quotas
- fixed per-task wall time and memory, retries and model token budget
- independent IFC validation, audited log and no hidden solution exposure

The trusted I0 manually authored reference implementations already exist in
tests/oracles/python/independent_ifc_oracle.py. They are run only by local
G1 parity tests, not given to the LLM as example solutions. An independent
native IFC comparator showed direct XML D0 versus trusted I0 geometry/
semantics/topology parity for six own synthetic tasks (#16).

## Offline, nonbilling reproduction

    uv sync --frozen --python 3.12
    .venv/bin/python -m tools.imperative_preflight_demo
    .venv/bin/python -m unittest tests.test_imperative_control -v
    .venv/bin/python -m unittest tests.test_oracle_parity -v

The command prints ACCEPTED_SOURCE_ONLY_NOT_EXECUTABLE for a benign code
snippet, matching original source IFC hash and no actual Python execution.
No output IFC, no API usage or official BIM-Edit score is produced.

## Unmet before Issue #18 closes

Real OS process/container sandbox #19; actual safe generated code execution
and output capture, independent evaluator #21; full six-class CRUD support;
verified licensed IFC corpus and matching full observations, actual model
client and durable budget/logging #20. Keep the primary 324-task gate BLOCKED.
Production Xim/BIXML is untouched.
