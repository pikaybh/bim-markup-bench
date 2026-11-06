# G0 #8 — Synthetic test model, answer firewall and rights review

**Status: G0 test contract with limitations; not a production-grade, process-level sandbox.** Do not run paid trials or untrusted LLM-generated Python in this environment.

## Independently created synthetic IFC4X3 fixtures

The source generator is tools/generate_synthetic_ifc.py. Run on pinned Python 3.12 and IfcOpenShell 0.8.4.post1:

- input.ifc — floor/site/building/storey, wall, slab, column, IfcSpace, window/door and two hosted IfcOpeningElements, IfcRelSpaceBoundary, containment/aggregation.
- expected_wall_height.ifc — same stable synthetic GlobalIds, declared wall geometry taller.
- expected_window_move.ifc — same stable synthetic GlobalIds, window and opening translated consistently.
- Each file is <100 KB. All files are generated from original made-up geometry/names; no third-party IFC samples or Xim code copied.
- IfcOpenShell 3D triangulation was observed for Wall (24 vertices, 48 triangles), Slab/Column/Door/Window (8 vertices, 12 triangles each) with openings.
- IFC2X3 / cross-platform parity and evaluator correctness remain UNTESTED.

## Strict answer visibility

The original BIM-Edit task record is for the grader only; it includes target GUID, input and reference IFC paths, evaluation annotations and task tags. The ONLY model-facing projection is a validated envelope with task_id, instruction and an isolated input filename exactly input.ifc. No ground truth, target GUID, evaluator source, expected output, private split, model hash or .env values can enter the visible payload.

Three compartments are proposed:
- agent/: only building.xml and language_spec.md are edit-capable/readable, input.ifc read-only.
- backend/: IFC compiler; read-only source and agent's committed source, writes candidate IFC to isolated output.
- grader/: GT IFC, scorer, private reference annotations. Completely absent from agent container and never included in the agent prompt.

src/security/agent_boundary.py currently provides a FAIL-CLOSED **mock allowlist and serializer contract** with positive/negative tests. It is NOT an OS-enforced sandbox. A Python process with the same OS permissions can still read arbitrary host files. Issue #19 MUST enforce real process-level filesystem mounts/ACLs, network off, child process denial and secret isolation. A prompt or mock tool check is not protection for untrusted generated Python.

XML safety preflight rejects raw DTD/ENTITY/conditional nodes and >2MiB inputs. Issue #10 must use an actual non-expanding XML parser with disabled external entities and independently enforce nesting depth and attributes; this byte screen does NOT substitute for that parser.

## License ledger

manifests/source_rights.json tracks provenance status. Every third-party IFC file defaults to NO redistribution until per-file terms, owner/source, consent and SHA-256 are verified. The BIM-Edit card says CC BY 4.0, but this does not prove each individual model can be republished without attribution/other restrictions. BIBIMBAP machine-readable test resources and the IFC-Bench model rights need independent audit (#5/#6). Only the deliberately synthetic tiny fixtures are checked for original authorship; their exact committed-file SHA-256 values are recorded in manifests/source_rights.json.

## Negative security tests

- GT, target GUID and raw file path elided from model-facing task envelope; injecting them as fields is rejected.
- Escapes including ../, absolute filesystem path, symlink to outside, .env reads, access to grader and evaluator denied by mock file allowlist.
- Network and shell tools never presented to direct-source-editing agent (mock denial tests); no actual untrusted Python is executed.
- DTD, XXE and overlong XML rejected by a byte screening contract; full parser under #10 still required.
- Unknown rights or absent consent block corpus redistribution.

## Explicit remaining acceptance evidence

1. Independent OS sandbox verification on target Mac/Linux/Windows (G2 #19): file mounts, network, inherited environment, command execution and symlink TOCTOU attacks.
2. Full IFC class/geometry/topology model support (G1) and actual read/write controlled runtime; these fixtures alone do not establish engine parity.
3. Per-file provenance and legally sharable corpus management (G0 #3/#5/#6), not simply a published dataset-level license.
4. Private grader process pipeline (G2 #21) and model log redaction under live API execution.

No API calls, benchmark scores or native BIXML/Xim code are produced by this work.
