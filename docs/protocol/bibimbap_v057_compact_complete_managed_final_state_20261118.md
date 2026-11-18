# v0.57 — Source-anchored **complete ManagedElements final-state** D variant and actual original-native IFC fidelity

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/229
**Exact stacked parent:** v0.56 [Draft PR #228](https://github.com/pikaybh/bim-markup-bench/pull/228) HEAD \`f9f18eb83d300e5ae2b0f0112f3de8b500fc992a\`.
**Experiment status:** engineering/source-native developer-control test **only**. Paid LLM trials 0; actual LLM-generated task solutions 0. The BIXML/Xim product, independent research \`main\`, original author repository, source IFC data and all earlier SHA-pinned results remain unchanged.

## 1. Explicitly NEW representation and why it is scientifically different

v0.55 **D_COMPLETE_XML** is a primary declarative state comparison arm that requires an LLM to output a **complete 39–172 KB XML** document, including repeated immutable source evidence, for one native IFC edit. v0.56 **D_COMPLETE_XML_STREAMED** preserves identical whole-document semantics but divides that document into up to 24 chunks, changing tool schema and feedback frequency. Both are scientifically distinct from actual **I_NATIVE**, which runs general Python/IfcOpenShell in a pinned OS-isolated Linux Docker worker.

v0.57 adds a **separately named, experimental D_MANAGED_FINAL_STATE** representation. The model receives the **exact same initial original source XML** as previous genuine D and I arms through the unchanged \`read_building_xml\` tool. Its NEW \`submit_managed_final_state(xml_text)\` tool accepts a tiny **complete final object-state declaration** for the entire *explicitly managed source-derived subset*, anchored by:

- immutable original IFC4X3/mm file SHA-256;
- SHA-256 of the full original canonical source-projected \`BuildingState\` XML;
- exact \`EXACT_ORIGINAL_SOURCE_GUID_SUBSET\` boundary and v0.57 identity;
- **every originally managed Slab/Column GUID**, in canonical source order, with its complete final numeric attributes and explicit \`present=true/false\` value.

The model does **not** emit an edit command, typed XML \`NativeEditPlan\`, Python code, target action list, partial patch, before/after diff or original source STEP/mesh/relations. Unlike earlier v0.50 membership deletion, missing GUID rows are **always rejected**. To delete a managed original Column, its complete original GUID row stays in the final-state document with \`present=false\`. The host does not invent omitted records, object identities, state values or private target GUIDs.

This remains a deliberately **partial IFC-backed managed state**, not lossless IFC/BIXML serialization. The frozen supported subset is only four **engineering-selected, nonrandom original** BIBIMBAP editing tasks (geometry_test_14/15 and topological_test_11/17) out of 45 original public editing tasks/31 unique IFC source hashes. The other 41 have **not** been attempted for matched original-edit model outcomes.

**The change in model output representation is a new experimental factor and is NOT retroactively equivalent to earlier D_COMPLETE_XML, D_COMPLETE_XML_STREAMED or I_NATIVE.** The source input remains byte-identical, but tool schema, output lengths, error surface and representation familiarity change. None of these engineering data are causal LLM performance evidence.

## 2. Trusted reconstruction and real native IFC commit

New runtime \`src/runtime/experimental_v57_compact_managed_state.py\`, strict v0.57 XSD and model-facing \`tools/bibimbap_v057_managed_final_state_session.py\`:

1. Read-only source projection is generated from **exact original IFC file hash and known four original public tasks**, never from a candidate or author GT. The compact XML must match the exact original source and BuildingState hashes. XSD and strict host parser reject unexpected elements/attributes/namespaces, DTD/XXE, duplicate/reordered/foreign/omitted GUIDs, wrong presence flag, partial numeric values, out-of-bounds values, unsupported Slab/managed-geometry deletion, and unsupported native edits.
2. The trusted host reconstructs the **whole** source-anchored \`BuildingState\` document, appends its original immutable STEP/GUID/relationships/geometry subtree, and includes exactly those final managed elements whose explicitly provided \`present\` is \`true\`. It validates this complete document using the original source v0.50 full-document diff/XSD/physical semantics. No server-side answer choice or editing command is exposed to the model.
3. The original v0.55 host then compiles the **actual original native IFC** through its preexisting trusted original source compiler, independent original IFC non-target and physical scope oracle, and real source-vs-result IFC4X3 schema-error multiset guard **before** promotion. This keeps the original source's one inherited schema issue distinct from newly introduced errors. No invalid native IFC can become \`output_ifc\`.
4. A malformed final state, no-op original state, exact previous accepted-state replay, or v0.55 one-shot bypass refuses with bounded generic errors. Last-good XML and IFC SHA remain byte-identical after rejection; source files are immutable. Exactly 25 total calls are available, and the original full source read tool is unmodified. The new compact edit requires one submission call.

The source-only model-facing host imports no original author scorer/GT, private target IDs, developer controls or provider client. **Author-repository grader execution is restricted to a separate evaluator-only audit.**

## 3. Actual original IFC results: output sizes and binary fidelity

We generated eight **source-derived developer controls** (one physically intended positive and one deliberately physically wrong-but-permitted negative per task). We independently passed their completed real IFC edits through both v0.55 D_COMPLETE_XML and v0.57 D_MANAGED_FINAL_STATE real original source-native compilers. Each matched source IFC SHA, real IFC output SHA, source-native physical/scope acceptance, IFC schema-delta acceptance and source-derived physical task predicate results. Original author repository \`execute_test\` Boolean metric values and mean score were separately executed on both IFCs and matched in all 8 pairs. These are **not** eight LLM completions, official published paper benchmark results or a prospective random 45-task sample.

| Original task | Existing complete XML (positive) | New complete managed final state (positive) | Python source-derived developer control | Full XML / compact bytes | Original author repository positive score |
| --- | ---: | ---: | ---: | ---: | ---: |
| geometry_test_14 | 39,602 B | **484 B** | 887 B | **81.82×** | 1.00 |
| geometry_test_15 | 60,846 B | **777 B** | 1,687 B | **78.31×** | 1.00 |
| topological_test_11 | 172,420 B | **567 B** | 1,634 B | **304.09×** | 1.00 |
| topological_test_17 | 151,758 B | **978 B** | 1,136 B | **155.17×** | **0.50** |

Negative control sizes are similarly small (493, 786, 571, 974 B), and original author repository negative metrics match between full and compact IFCS (0.667, 0.667, 0.667, 0.000). The task17 valid deletion's **author-repository score 0.50** remains unchanged and independently distinguished from IFC physical correctness, because of the previously established author non-target-root cascade helper discrepancy.

**Byte size is NOT provider token size**; these Python snippets and XML states are independently authored developer controls, and differing semantics and tool affordances are not magically matched. The new complete final state happens to be smaller than these developer Python snippets in all four cases, but no inference about LLM coding/editing accuracy or billed token parity is permitted.

**Initial model source read** remains unchanged from genuine D and I: 39,611; 60,856; 172,424; 151,968 UTF-8 bytes respectively. New model-facing compact tool JSON schema is **1607 bytes**, versus v0.55 D whole-document tool **1324** and I-native **1255** bytes. This input and tool-schema overhead must be accounted for in a prospective provider tokenizer/billing study. A compact output alone does NOT eliminate large source reading/context overhead.

## 4. Security, completeness and atomicity tests

Focused tests include source/original-state SHA spoofing, unknown/duplicated/reordered/missing GUIDs, omitted deleted objects (no partial patch), foreign attributes/namespaces, invalid numeric data, NaN/Infinity, mixed mapped shared depth, unsupported Slab or geometry-bearing Column removal, absent/misordered object values, XXE and DTD, unexpected text/nested elements, oversized payload, original no-op, exact state replay, misuse of original whole XML tool, 25-call exhaustion, and forced independent native schema rejection. Bad submissions are not allowed to change the last valid native IFC, current committed XML or original source file. Actual original-four positive/negative native cases (8 pairs) include independent evaluation of physical correctness and exact original author repo scoring in evaluator-only code.

This strict bounded schema and known original managed subset must not be called full IFC semantics, a model-generated solution, or a guarantee of global EXPRESS compliance. The v0.55 native schema validator runs \`express_rules=False\` and therefore is a **source-error-delta validator**, not a proof of all schema constraints.

## 5. Data rights, cost and experiment admission unchanged

The public Hugging Face dataset card metadata observed 2026-11-18 for \`clemenskujat/bibimbap-data\` at revision \`f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca\` declares \`cc-by-4.0\`. It does **not independently prove** rights/attributions for all original IFC third-party assets, authorize uploading the data to a provider, or license original author source code \`nbharathik/bibimbap\` Git \`667004e16bd38fd7d538bcee56191465429fd975\` (the pinned checkout contains no recognized LICENSE). No original author test source, IFC file, hidden GT, private target IDs or answer code is copied into this research repo or sent to a model.

Hard **NO MODEL LAUNCH** v0.57 admission remains unconditional, even if passed an all-true fictional approval object. There is no provider credential, client, API call, billed token receipt, USD budget authorization, approved exact model snapshot, source-transfer permission, or actual LLM-generated benchmark outcome. The formal D vs I causal study remains **BLOCKED** pending independent source rights, informed consent, scorer-version review, real provider-billed D/I context/output tokens, decoding/feedback budget parity and an explicitly accepted preregistration.

## 6. Frozen repeatable evidence

Files added:
- \`spec/original_native_managed_final_state_v057.xsd\` — strict compact complete-state grammar.
- \`src/runtime/experimental_v57_compact_managed_state.py\` — immutable original-source projection, strict complete-roster parsing, trusted full-state restoration.
- \`tools/bibimbap_v057_managed_final_state_session.py\` — new source-scope-native/schema-validated atomic v0.57 host.
- \`tools/bibimbap_v057_provenance.py\` — original rights pin and unconditional no-paid-launch gate.
- \`tools/audit_bibimbap_v057_compact_managed_final_state.py\` — developer-side original actual IFC and original author evaluator replay; never model-facing.
- \`tests/test_bibimbap_v057_compact_managed_final_state.py\` — 50 focused positive/negative tests.
- \`reports/bibimbap_v057_compact_managed_final_state_original4_20261118.json\` — frozen controls and actual author-source metrics.

Frozen v0.57 report SHA-256: **22b3f30166ba2164278cdc1b2b25e5e4c4d0d0cddb74c25f7b759287bd127e57**.

Frozen parent v0.56 full XML report SHA-256: **09b2435f402fd333cdb048681313b05a180fe751bc641b9a8a774b77d7620849**.
Frozen v0.56 rights/model gate SHA-256: **6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c**.
Frozen prior v0.55 actual Docker report SHA-256: **e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c**.

Offline local reproduction in an independent Windows research worktree with installed original IFC/author checkout, without model provider or network:

    python -m tools.audit_bibimbap_v057_compact_managed_final_state --check
    python -m unittest -q tests.test_bibimbap_v057_compact_managed_final_state

The audit's \`--check\` **rebuilds actual native source IFC outputs** and reruns 16 evaluator-only original author source tests, confirming exact report-byte equality; \`--write\` creates the report exclusively (never overwrites earlier frozen reports). A failed replay is a hard failure, never a claim of successful model execution.
