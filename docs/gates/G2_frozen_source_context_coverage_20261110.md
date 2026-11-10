# G2 #20 — Frozen 36 source-only D/I observation coverage (2026-11-10)

**Status: BLOCKED FOR G3, irrespective of local source-context checks.**
No LLM calls, official IFC scoring, generated Python execution, provider
billing, ground-truth reading or benchmark mutation.

## Why this matters

Matched source observations are necessary (not sufficient) for isolating the
markup-vs-Python representation intervention. Earlier offline G2 audits
checked one real IFC. This read-only check covers every currently verified
conditional source among the original frozen 36 candidate tasks, without
changing the candidate selection:

- 23 legacy v0.1 static-unsupported tasks: explicitly NOT context-tested.
- 2 conditional tasks without a currently verified original IFC: blocked.
- 11 pinned conditional source IFCs: try comparing actual D/I source views,
  retaining every failure and never counting these as solved tasks.

Original published task data and fixed candidate sample SHA-256 hashes are
checked before any projection. Every actual original IFC is checked against
pinned remote Git/LFS content digests. Only public task ID, task instruction
and source IFC path are read for staging; hidden target, evaluation annotation
and ground-truth IFC are not used. Grader-only IFCs are never opened.

The existing G2 direct-markup and imperative source adapters produce model
observations. The audit verifies byte-identical task ID, instruction, v0.1
source XML, XML specification and source IFC digest. It records each common
string as UTF-8 bytes, codepoints and hash, and separately fingerprints
the I-arm API-reference notes. No raw task prompt, hidden target GUID, native
IFC file path or candidate solution is printed or persisted.

Unreadable/altered IFC bytes, projection error, common source mismatch,
unexpected execution permissions and forged hash produce BLOCKED, not PASS.
Temp workspaces are isolated for each source.

## How to reproduce on Windows 11

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_frozen_context_parity -v
    .\.venv\Scripts\python.exe -m tools.audit_frozen_context_parity --output-json reports/g2_frozen_context_parity_20261110.json

The evidence tool returns exit 2 intentionally, EVEN when every eligible
source-view check passes. It refuses to overwrite an existing report.
No model provider, Docker daemon, network or held-out scorer is invoked.

## Observed read-only result (2026-11-10)

- 36/36 frozen candidate IDs accounted for, without reselection.
- 23 static unsupported tasks retained, not silently tested as successes.
- 2 conditional tasks missing pinned source IFC bytes; no download performed.
- **11/11** available conditional original IFCs produced identical common D/I
  source-text fingerprints; zero context projection failures in this check.
- This is **0 official edit tasks scored, 0 live LLM calls and 0 full D0/I0
  task approvals**. It establishes only common source-text parity.
- Five new direct regression tests first passed; after additional remote-tree
  and prior-report digest pins, negative tampering tests were added.
- Sanitized evidence: reports/g2_frozen_context_parity_20261110.json.

## Limits (critical)

1. These two adapters share source-projection code; equal text does not prove
   independent semantic completeness, missing-information parity or fidelity.
2. The I-arm necessarily has additional API instructions and a different
   authoring interface. Actual provider wire-format tokens, prices,
   feedback budget, tool execution and runtime parity are NOT verified.
   UTF-8 bytes must not be converted to guessed model tokens.
3. The 23 unsupported and 2 uncached tasks remain in the fixed denominator.
   A conditional source observation is not a D0/I0 task oracle or evidence
   that either authoring arm can complete an instruction.
4. Current Linux Docker worker admission is blocked. No generated Python
   executes; no LLM inference or scored benchmark comparison occurs.
5. Official BIM-Edit evaluator provenance/parity and individual IFC source
   rights remain unresolved. An independent scorer is not the official one.
6. Experimental v0.2 Space metadata is NOT promoted to either live model
   context. That would alter the treatment and require a revised protocol.

## Next scientific gate

Review any source failures without consulting held-out reference solutions;
independently establish the correctness and sufficiency of the projected
public BIM context; verify real tool isolation, tokenizer/provider envelopes
and independent scorer provenance, and review data rights. Preregister an
eligibility rule before measuring outcomes. Never infer XML effectiveness
from this engineering preflight.
