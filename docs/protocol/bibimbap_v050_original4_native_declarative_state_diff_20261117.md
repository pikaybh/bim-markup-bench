# v0.50 — Original four IFC direct declarative state-diff editing

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/215
**Stack:** v0.49 Draft PR #214, exact base 58226ef089d55e9ed630cd3e3152b5c1048a90db.
**Scientific claim:** original-source native IFC *D-state* engineering feasibility. **NOT** an LLM model comparison, an original-author benchmark score, a generic IFC authoring system, or the final BIXML product language.

## Research problem and causal-arm identity

The primary hypothesis requires the LLM to edit final declarative document **state**, never to emit typed commands inside an XML wrapper. v0.45/v0.47 proved a restricted typed-XML operation interface (T-XML) and restricted AST Python interface (T-Python); v0.49 correctly rejected their promotion to primary D-state-versus-I-native evidence.

This v0.50 implementation introduces a separate **D-state** surface on four exact original IFC4X3-native-millimetre input sources. It returns a complete XML snapshot with an immutable OriginalNativeIFCSource, preserving all original literal STEP DATA and native source products, relations, properties, materials, placements, physical world meshes as v0.44 already did, and a new explicit **ManagedElements** final-state overlay. A model edits only the latter; the immutable original source is never changed. Source outside that managed scope is preserved as opaque native IFC assets and must never be implicitly deleted.

Example *schematic* tree (no source-/task-specific answer is included):
- BuildingState: root version 0.50, original source SHA-256, native schema IFC4X3, native unit MILLIMETER and representation DECLARATIVE_STATE_SNAPSHOT
- OriginalNativeIFCSource: fixed actual source IFC read-only tree
- ManagedElements, boundary EXACT_ORIGINAL_SOURCE_GUID_SUBSET:
  - Slab with stable ifcGuid plus final dimXM and dimYM in metres; or
  - Column with stable ifcGuid and final worldXM/worldYM or extrusionDepthM; or
  - Column with stable ifcGuid only, where removal of an original managed element declaration means absence from final managed source state

**No model-facing NativeEditPlan, Set*, Move*, Delete*, Create*, Python calls, IFC API, generic code execution or geometry operator.** A trusted compiler infers the change from original/source and edited final XML snapshots, using existing GUIDs and a declared bounded managed scope.

This is an **IFC-backed partial source overlay**, not source-free complete BIM or lossless BIXML serialization.

## Exact original 4 task capabilities

| Public original task | Source-derived managed final-state view | Permitted before/after difference |
| --- | --- | --- |
| geometry_test_14 | Existing one Slab, final dimXM and dimYM | Exactly one native source rectangle dimension strictly increases |
| geometry_test_15 | Existing four Columns, world XY final centres | Exactly one Column world XY moves; parent-local IFC frame conversion is performed inside trusted compiler |
| topological_test_11 | Existing two mapped Columns, final extrusionDepthM | Both final depth values change identically; original mapped source body is shared |
| topological_test_17 | Existing ten Columns, explicit stable-GUID membership | Remove 1–9 managed Column declarations, preserving all others unchanged |

Supported transformations are source-shape/IFC-schema constrained; creation, unmanaged deletion, arbitrary Pset/material/topological edits, arbitrary IFC geometry/classes, unmatched source or cross-file references are unsupported and rejected. A no-op is not reported as a successful native modification. Existing original author/source input file SHA and original public question SHA pins are unchanged. The original 45 edit questions, 15 CREATE/15 UPDATE/15 DELETE and 31 unique IFC source hashes remain the true public benchmark population; these four task rows are a previously chosen engineering subset, NOT prospective random sample or confirmatory denominator. Other 41 tasks are not attempted.

## Trusted model runtime boundary

Files:
- spec/original_native_declarative_state_v050.xsd — new strict schema
- src/runtime/experimental_v50_original_declarative_state.py — deterministic project, validate and infer source before/after final-state semantic diff
- tools/bibimbap_v050_direct_original_state_session.py — separate model-facing two-tool read/submit interface
- tools/audit_bibimbap_v050_declarative_state.py — developer-only source-based actual IFC positive/negative evidence and immutable reporting
- tests/test_bibimbap_v050_original_native_declarative_state.py — focused safety, real IFC and negative regression tests

The model-facing session offers only read_building_xml and submit_building_xml, limited to **25 total calls** and entire XML replacement. It does not import developer positive controls/benchmark grading and returns neither target GUID suggestions nor private evaluator results. Every call verifies the original IFC bytes remain pinned. The XML parser uses DTD/XXE/network/huge-tree disabled validation; strict XML XSD, bounded XML bytes, stable GUID roster, immutable original source subtree canonical comparison, unique identities, canonical original order and micrometre-precision finite value restrictions. A failed request never overwrites the previous valid XML or IFC.

The **trusted compiler, outside the LLM**, lowers an inferred semantic difference to the previously validated private v0.45 original-native-mm mutation backend. This internal, task-bounded plan is NEVER included in model-visible XML or tool responses. A fresh source-native IFC candidate is written to isolated scratch; an independently implemented v0.45 source/physical oracle reopens the actual IFC and verifies source GUID/relationship/untouched geometry and bounded native edits. Only then does the host commit current XML and candidate IFC. This reuse of the IfcOpenShell backend is valid D-state trusted runtime behavior; it does not grant any BIM command API to the D-arm LLM.

Original IFC native length is **millimetres**; model-managed state fields are in **metres**. Source world physical mesh vertices produced by IfcOpenShell.geom are *already in metres*, never divide those mesh values by 1,000 a second time.

## Real original source native developer controls

A completely separate developer-only audit converts the frozen v0.48 public-source-derived controls into final declarative replacement snapshots. These private demonstration values (including source-suggested positions/deletion sets) are NEVER mounted in the model-facing session or copied into its tool descriptions.

For each of the four original public IFC sources, the audit runs source-real **positive and negative research physical predicate controls**. For each control it writes a real native IFC from v0.50 D-state, verifies it with the independent v0.45 native IFC physical/source oracle, and independently writes a second native IFC through the old v0.45 T-XML backend using the SAME developer control. The two actual native candidate files are byte-SHA-identical for all eight pairs. A separate v0.48 task-specific source physical predicate passes all four developer positive cases and rejects all four intentionally non-solution native edits; an unrelated native edit is not automatically a correct original task solution.

**Result:** 8 actual D-state source-native IFC candidates, 8/8 physically independent IFC checks, 8/8 byte-identical counterpart T-XML native candidate IFC files, 4 research-semantic-positive developer controls, 4 research-semantic-negative developer controls. **Zero actual LLM model calls, zero original author grader invocations, zero hidden GT, zero Docker/paid provider calls.** None of the controls establishes an original author benchmark score or comparative D/I-native LLM accuracy.

**Frozen machine report:** reports/bibimbap_v050_original4_declarative_state_diff_20261117.json
**SHA-256:** eb6bef852eabf12ed76b5c5df861a8e5a355a5142e5ad0d3732d646b25dfb28a

This report intentionally does **not** store developer solution target GUIDs, numeric edit values, private typed plans or revised source XML content. Report has source/question SHA, source/manifests and real native candidate SHA plus predicate outcome. Report is created once with --write and re-executed/byte-compared with --check; never overwritten. Exact prior frozen report hashes verified unchanged:
- v0.45: 7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3
- v0.48: ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08
- v0.49: 14a3dd1bd2a00c4fbd7efdafca88c89d00b7c4d247152782d53055b494d54478

## What this does NOT establish

This is **D-state D0 developer feasibility** for a previously selected narrow native source subset. It does not prove the D-arm LLM can solve these tasks, that an independent original benchmark author evaluator agrees with our physical research oracle, a true I-native Python/IfcOpenShell execution baseline, unrestricted source/edit authority parity, equal paid provider tokens/context/prompt budgets or the causal effect of source representation.

**Next priority:** build an executing, OS-isolated genuine Python/IfcOpenShell **I-native** arm that independently reads the same four source IFCs and can express the same original physical/task edits, with independent source/native IFC oracle and no hidden GT access. Define and freeze actual model-facing prompts/provider/token usage and scorer provenance only after both actual arms are validated. No paid paired model trial without explicit approval/budget and independently demonstrated fairness.

## Offline local reproduction

Windows isolated worktree: D:\문서\D__1_Projects\202611\bim-markup-bench-issue215-declarative-state-diff

Shared Python environment: D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe

Run using that Python interpreter:
- python -m unittest -q tests.test_bibimbap_v050_original_native_declarative_state
- python -m tools.audit_bibimbap_v050_declarative_state --check

All real IFC generated candidates are ephemeral developer-only scratch outputs; source IFC files, original public questions, previous frozen evidence, research main and the unrelated Xim/BIXML product remain untouched.
