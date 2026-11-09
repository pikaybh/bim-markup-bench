# G1 #16 — fixed BIM-Edit 36-task source-only D0/I0 feasibility audit

Date: 2026-11-09 · **BLOCKED — no official paired D0/I0 task oracle proven**.

## Research boundary

This is a **pre-model, pre-grader, read-only source capability** audit of the original metadata-fixed 36-task candidate. It never changes the task list, selects a subset for scoring, runs an LLM, sends a provider request, reads hidden reference IFC, opens a public benchmark ground-truth file, writes an edited IFC, or claims official scores. Trusted task target GUIDs from the frozen grader-only metadata are inspected in a private process *only to test native eligibility*; no GUID, reference path, source path, raw prompt, computed solution or IFC bytes are emitted to the report.

The source-only checks distinguish an already known static engine blocker from additional read-only native source preconditions. Even an eligible source predicate is **not** evidence of semantic task understanding, exact proposed edit, paired XML/Python oracle parity or benchmark correctness.

## Observed 36-task breakdown

| Disposition | Count | Meaning |
| --- | ---: | --- |
| STATIC_ENGINE_UNSUPPORTED | 23 | G1 metadata-only capability cannot satisfy requested class/operation |
| MISSING_PINNED_INPUT_IFC | 2 | Two of the conditional cases lack currently cached original input IFC |
| WALL_DELETE_SOURCE_DEPENDENCIES_BLOCKED | 2 | Existing walls have connections, spatial boundaries, and/or other inverse dependencies |
| WALL_THICKNESS_NATIVE_DEPENDENCIES_BLOCKED | 3 | Existing wall type/material/boundary/connection dependencies violate safe thickness edits |
| WINDOW_DELETE_NATIVE_RELATIONS_BLOCKED | 2 | Window material, type, boundary, or other native inverse relations exceed allowed deletion subset |
| OPENING_MOVE_NATIVE_FRAME_OR_DEPENDENCY_BLOCKED | 1 | Existing host placement is rotated; bounded opening relocation refuses it |
| WINDOW_OPENING_DIMENSION_CHANGE_UNIMPLEMENTED | 1 | Existing width-change instruction is outside compiler capability |
| REQUIRED_NATIVE_RELATION_CREATION_NOT_IMPLEMENTED | 1 | Required IfcRelConnectsPathElements and/or IfcRelSpaceBoundary creation is unimplemented |
| WALL_CREATE_SPATIAL_ORACLE_NOT_PROVEN | 1 | Could not independently reconstruct task placement and verify D0/I0 against source, so remains unproven |
| **Official task D0/I0 fully proven** | **0** | **No scored LLM experiment authorized** |

Summary: 23 static unsupported, **11 locally byte-verified conditional source inputs inspected**, 2 conditional source inputs missing. **10 of 11 inspected cases have explicit local blockers**; the remaining one is an unresolved spatial wall creation, not eligible by default.

## Reproduction (Windows / no network)

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_pilot_source_eligibility -v
.\.venv\Scripts\python.exe -m tools.audit_pilot_source_eligibility --output-json reports/g1_frozen_source_eligibility_20261109.json
```

The audit CLI returns **exit code 2 by design** and emits only sanitized task IDs, operation, category, class, boolean checks and reason codes. It must NOT be made to return 0 until genuine paired deterministic, independent IFC validation is available. The report itself is a static read-only evidence ledger and is not accessible to either future LLM agent.

The script verifies hashes of any cached conditional task IFC input, refuses missing or changed frozen task manifests and uses the actual conservative compiler preflight functions. It does not call `compile_declarative_xml` to publish a candidate output. The status `GT_file_loaded:false` is a tooling claim about this audit command only, **not** proof the system's complete future LLM sandbox is secure.

## Next correct work

The *first* task-level G1 goal is to create one **independent, fixed, real-source D0 and I0 deterministic oracle** without referencing GT in the model authoring environment. Predeclare its exact intended geometry, relations and source checks before running either authoring mode. Do not treat the spatial wall creation as proven based on the ability to project source IFC alone. For broader coverage, implement rotated host-Opening moves, source IFC relations and safe native wall joins as reviewed geometry/topology features, maintaining original file preservation and opaque asset boundaries. Align the scorer with a verified public source or keep all reported scores tagged independent.

## Dependencies and related PRs

- #11 / Draft PR #64 fixes a real IFC floating-point XML serialization issue; this audit branch stacks on that pending change.
- #4 / Draft PR #62 audits paper vs independent scorer; official evaluator provenance still not verified.
- #3 / Draft PR #63 audits six large missing IFC pairs and per-model rights. No additional model bytes were downloaded by this audit.
- Third-party independent replication confirms an official evaluator source availability problem: https://ai.onestruction.com/leaderboard/en/methodology/ (BIM editing → Evaluator). This does not establish numeric equivalence.

This is **0 official tasks scored, 0 provider calls and 0 demonstrated LLM performance**. The existing fully synthetic D0/I0 oracle tests remain valid but are not substituted for missing real-task evidence.
