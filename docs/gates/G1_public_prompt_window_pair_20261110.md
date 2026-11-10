# G1 #16 — Public-prompt-derived Window/Opening D0–I0 native pair

**2026-11-10 · PASS_PROMPT_DERIVED_SOURCE_ONLY_PAIR_OFFICIAL_TASK_STILL_UNVERIFIED**

This one-task G1 developer-owned reference oracle fixes an important deficiency of the previous manual Window move demonstration: **it derives the GUIDs, distance, world direction and preserve-relations requirement from the unchanged public task instruction**, not the grader-only target annotations or a developer preselected displacement. It is not an LLM result, official BIM-Edit score or G3 authorization.

## Frozen evidence

- Task ID: WIN-UPD-DIR-A-002, an unchanged member of the original 36 candidate.
- Task JSONL SHA256: 9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83
- Frozen candidate SHA256: 75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694
- Native original input IFC SHA256: c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9
- Public instruction SHA256: ff98d90daafa34a4979fc942d4d3477a0128526a2cf7c918c419473319078efe
- Prompt explicitly identifies both IFC Window/Opening GUIDs, specifies **world +Y by 1m**, and requires existing relationships to be preserved.
- The restricted exact-instruction parser rejects unsupported axes, magnitudes, extra directives, unrecognized grammar and malformed/duplicate GUIDs rather than guessing.

## What actually runs

**D0:** The existing source-only direct authoring workspace exposes the actual v0.1 building.xml, public instruction, and schema. The prompt-derived Opening GUID must appear exactly once in XML and the prompt-derived Window GUID must link to it. A trusted deterministic G1 helper rewrites only the declarative Opening offset. The real SourceOnlySession validates this document state; its separate TrustedCompilationController produces IFC *outside* any model loop. The XML contains no command-list operations.

**I0:** The independently authored IfcOpenShell Python reference recipe takes the Opening GUID **derived from the public prompt**, validates a unique native Window–Opening–host Wall chain, computes the host-local displacement from the public world-vector using the actual native host frame and edits its IFC Cartesian location. It imports no D0 compiler, parser or binder. Each output is temporary and neither result is copied into a model-facing context.

The actual common D0 and I0 G2 observations are independently constructed and verified **byte-identical** for task ID, public instruction, original v0.1 XML, schema specification and source IFC SHA. The I0 source context has **1,113 extra bytes of API notes**; equal provider-token spend, tool access and execution feedback are **not** established.

## IFC proof beyond a matching displacement

| Property | Verified observation |
| --- | --- |
| Source IFC native entities | 2,833 |
| Source IfcRoot objects | 250 |
| D0 and I0 changed native entity count | Exactly 1 each |
| Changed entity | Only the intended Opening's IfcCartesianPoint |
| Window AND Opening world translation | Exactly the public instruction (tolerance 1e-6m) |
| Native IfcRoot GUID inventory | Identical to source |
| Existing IFC relation inventory | Identical to source |
| Independent six-category IFC D0/I0 observation comparator | Pass |
| D0 full IFC SHA256 | 10c68b5a1320f51e1f75f0e12868e1b38f84bc316a92a3c123059d0358bdfe16 |
| I0 full IFC SHA256 | 10c68b5a1320f51e1f75f0e12868e1b38f84bc316a92a3c123059d0358bdfe16 |
| Original IFC bytes | Unchanged |
| GT/reference IFC read, official scorer run, LLM/provider calls | **None** |

The pair reproduces the earlier manual reference output hash, but the new verifier **never reads the earlier report** to construct the result. An adversarial unit test provides a forged private target, ground-truth path and evaluation annotation: the new pair still derives identical native edits solely from the public instruction/source IFC.

The structured report contains task ID, hashes, matched shared-context byte counts and status flags, **not the prompt text, native target GUIDs, hidden GT paths, raw IFC source or candidate code**.

## Reproduce

Working directory: D:\문서\D__1_Projects\202611\bim-markup-bench

- Windows: .venv\Scripts\python.exe -m unittest tests.test_prompt_grounded_window_pair -v
- Windows: .venv\Scripts\python.exe -m tools.verify_prompt_grounded_window_pair (expected **exit 2**: official/full-model gate blocked)
- Windows: .venv\Scripts\python.exe -m unittest discover -s tests -q

Files:
- tools/verify_prompt_grounded_window_pair.py
- tests/test_prompt_grounded_window_pair.py
- reports/g1_prompt_grounded_window_pair_20261110.json

Negative cases include wrong amount/direction, ambiguous/extra directives, nonexistent native GUID, class mismatch, forged target/GT metadata, changed unrelated native IFC entity, mismatched D/I shared observations, and modified frozen source/task manifests.

## Scientific boundaries

The exact public prompt is interpreted here by **a deterministic manually implemented parser**, not an LLM. The output is not a blind score against the held-out official target IFC. The frozen 36 are still only candidate tasks, and no G1/G2/G3 official release or paid model call is approved. The untrusted imperative Python execution sandbox is unavailable until genuine Docker Linux kernel validation. Official scorer and per-IFC rights remain unverified.

The next frozen spatial Wall case, WAL-CRE-SPA-A-003, still lacks prompt-justified new room Name/Type/Psets/QTO and approved live v0.2 metadata authoring. Matching a developer-synthetic new room is not proof of the official intended result. No guessing/new room metadata copying should be promoted.

**No source IFC/GT/pilot manifest, existing scoring formulas, Xim or BIXML files modified.**
