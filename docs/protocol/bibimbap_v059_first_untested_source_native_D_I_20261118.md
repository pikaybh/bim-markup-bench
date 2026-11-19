# v0.59 — first unseen-source original IFC native task across full D, compact D and genuine Docker Python I

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/233
**Stacked parent:** v0.58 [Draft PR #232](https://github.com/pikaybh/bim-markup-bench/pull/232), exact parent commit `c8f66d4839e038d4edf481d44de71cbe98eaf6c3`.
**Project scope:** independent `pikaybh/bim-markup-bench` research. NOT Xim/BIXML product; no research `main` merge, no original author's source code or IFC dataset changes, no GT/author scorer in model-facing tools and **zero actual LLM-generated or billable model tasks**.

## 1. Preserving all six original-source selections and actual native source requirements

v0.58 registered six previously untouched original-source SHA clusters one per geometry/topological x create/update/delete stratum, without observing any actual LLM result. They remain **unchanged and in frozen order**, not quietly replaced by easier tasks.

| Frozen original task | Real native IFC format and source entities | Source-question edit class | v0.59 admission |
| --- | --- | --- | --- |
| `geometry_test_03` | IFC2X3, 3 walls | Create door in related north wall; wall opening, void and fills | **NOT SUPPORTED** — IFC2X3 schema/scope and door/opening semantics |
| `geometry_test_13` | IFC4X3, 2 windows + 2 openings + proxy details | Move qualifying window +3m in world X; retain opening/window consistency | **NOT SUPPORTED** — placements, hosted opening and decorations |
| `geometry_test_19` | IFC4X3, 7 windows + 7 openings, 8 walls | Delete 2 windows opposite a named wall, linked opening/void/fill cleanup | **NOT SUPPORTED** — two-target identification and cascading cleanup |
| `topological_test_05` | IFC4X3, 7 walls + 2 slabs | Create exterior-access door and opening with topology | **NOT SUPPORTED** — actual door/host/opening geometry |
| `topological_test_12` | IFC4X3, 8 walls, 2 columns, 2 slabs + space | Shorten exterior-selected original wall 1m; connection/physical scope preservation | **NOT SUPPORTED** — exact native extrusion/profile and wall joins |
| `topological_test_18` | IFC4X3, 7 walls + 3 rooms (`IfcSpace`) | Delete the room enclosed by six named original walls, clean linked metadata | **NATIVE SOURCE-SCOPE AND SCHEMA ADMITTED**, developer controls only |

**New source-aware native editing eligibility: 1 of 6 previously untested tasks**. Previously verified 4 original source tasks (v0.55–v0.57) remain unchanged, for **5 task-specific developer-control cases total out of 45 original editing tasks**; the remaining **40 are not currently validated** by this version's exact source/task-native admittance. One of the other five still requires IFC2X3-aware source-schema and native geometry handling. Nothing in this checkpoint implies full 45-task parity or the ability to run the still-ineligible six-case LLM comparative study.

### Holdout contamination disclosure

The pre-selected v0.58 task was prospectively selected **before any LLM outcomes**. But in v0.59 we inspected the source and built developer positive/negative native fixtures for `topological_test_18`. That original source is therefore **now development-exposed**, not an untouched independent research holdout. We have not altered the v0.58 selection or removed the task from the denominator. A future confirmatory original-source unseen holdout requires a fresh explicitly versioned, independently frozen plan from remaining data or an honest development-set pilot label. **Do not claim these same six remain all untouched after this implementation.**

## 2. A genuine bounded declarative state, not a typed editing command

The new v0.59 source-only XML generator hashes the immutable original IFC4X3/mm source and reads actual mesh world geometry (in metres) for **all 14 original products**. Each source product is projected with original GUID/class/name and finite bounded world bbox where geometry exists. Source-only evidence is **not** model-visible original author targets, hidden grading or editing instructions.

**All three arms read exactly the same original model-facing `BuildingState` XML (3,143 UTF-8 bytes)**:
- `D_COMPLETE_XML_V059`: submit the **complete final-state `BuildingState` document**, keeping the original `OriginalNativeIFCSource` subtree byte-canonical-equal, original SHA, native IFC4X3/mm and complete all-3-space managed roster. Set exactly one original Space `present=false`, other two `present=true`; omission is **not** deletion and never silently backfilled.
- `D_MANAGED_FINAL_STATE_V059`: submit a compact **complete all-3-space final-state** declaration (baseline 580 UTF-8 bytes), with original IFC SHA and source full-state SHA pinned. Every original GUID appears in order with explicit presence. The trusted host reattaches the unchanged source geometry/bounds subtree, reconstructs the full declarative XML and validates it before any physical edit.
- `I_NATIVE_DOCKER_V059`: execute arbitrary native Python/IfcOpenShell in the already pinned Linux Docker sandbox (uid 65534, no network, read-only root, no caps, bounded CPU/memory/pids and two attested mounts), with explicit `commit()`. This **actually executes Python** and uses the original native IFC as input, not an AST-only or copied-output double.

All three use the same *task-bound* independent post-edit IFC oracle in `bibimbap_v059_topo18_native.py`, which enforces **exactly one original `IfcSpace` removed; no new rooms; no unexpected root, relationship, property, material, geometry or other native STEP entity modifications**, and the v0.55 **original-source-vs-candidate incremental IFC4X3 schema-error multiset must introduce zero new findings**. The expected legal deletion cleanup is derived by a separate *trusted* fresh source-only `ifcopenshell.api.root.remove_product` reference for **whichever** original space was removed, not the model's code, XML edit instructions or the hidden grader. All other native entities are compared by IFC ID/type and normalized direct attribute/reference signatures (STEP float text roundtrip tolerance 1e-6). No model target is chosen or published by the host.

**Important generality limitation:** this conservative admissible native representation can reject alternative otherwise-semantically-valid IFC encodings which rearrange STEP IDs or use a different cleanup strategy; it is an engineering source-scope verifier and can bias genuine I-native compared with fully general Python, not an officially graded universal correctness oracle. Identical initial XML/read tool does **not** imply equivalent editing affordances, costs, model billed tokens or information access: I can introspect the full original IFC in Python, while D has an explicit managed/projection subset. Any future causal claim would need to handle these differences.

## 3. Real source-derived public task physical result versus original author metrics

The original public question lists six wall GUIDs; **only the evaluator-only developer audit** reads the public question text and derives candidate room contact. It uses actual original IFC mesh vertices in world metres and tests intersection against source-only wall mesh bboxes with 5 mm tolerance. Exactly **one of the three source rooms** touches all six named walls; the other two fail source contact. No hardcoded target GUID or original author evaluator private answer was used. The result is a source-derived **independent research physical predicate**, not a claim of exact published paper scoring parity.

We ran **all three original source-native IfcSpace-removal developer controls in each arm**, resulting in **9/9 actual IFC candidates**:
- **3/3** complete-full-XML D source-native compiler commits;
- **3/3** compact-complete-state D source-native compiler commits, each output IFC SHA256 **byte-identical** to its same-room full-D counterpart;
- **3/3** *genuinely executed pinned Linux Docker Python* IfcOpenShell edits, each admitted by the same source/task-native scope and IFC schema-delta oracle.

All candidates have exactly one deleted original Space, source-linked metadata cleaned, other IFC entities preserved, no newly introduced IFC schema errors and untouched original source SHA. D and I native file bytes can differ because of independent serializer output, but exact native source semantics and original repository grader metrics agree on every corresponding edited room. The task grader is imported **only inside the separate evaluator-only audit**, never in model-facing host; there are no paper-official scores or model results.

| Source-only geometry classification | Original source room controls per arm | Original author repository score per arm |
| --- | ---: | ---: |
| Touches **all 6** public-question walls | 1 | **0.50** |
| Does **not** touch all 6 public-question walls | 2 | **0.00** |

The physically correct source-wall-contact deletion score **0.50 rather than 1.00** is a *material discrepancy*; it is NOT silently changed to 1.0. The exact published-paper scorer revision remains unverified. Independent physical correctness, original author-repository Boolean metrics and IFC source/schema admissibility remain different outcome layers. This source-only geometry predicate can itself miss semantic room/topology subtleties and requires independent review before serving as a definitive benchmark grader.

**Adversarial actual Docker checks:** a real worker that performs low-level `ifc.remove(space)` and calls `commit()` is refused by the host's independent native/scope oracle without setting `output_ifc`. Another real worker session performs a valid original room deletion and then tries to delete another room, which violates the exactly-one-space contract; the invalid candidate is discarded and the previous native IFC SHA remains **byte-for-byte unchanged**. A D full-state session similarly retains its previous committed native IFC and XML after a submitted document with a missing managed room row. No raw Docker source/GT or worker answer content is promoted to model-visible output.

## 4. Scientific, license, model and experiment admission barriers remain

The original BIBIMBAP code source `nbharathik/bibimbap`, pinned Git `667004e16bd38fd7d538bcee56191465429fd975`, has no recognized `LICENSE` in the checkout. A read-only public Hugging Face card at revision `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca` says `cc-by-4.0`, but this declaration does not independently prove every source IFC creator's rights, required attribution or grant provider upload/retention approval. The original evaluator modules and private target/GT are **not** in model-facing tool code or public research report.

The six v0.58 selected original tasks have **not** completed cross-arm native support. There is no approved exact provider/model snapshot, tokenizer, context/output limits, actual billed D/I token or USD budget parity, original IFC-to-model data transfer approval, prompt/tool feedback/error equivalence, independent source/metric preregistration or trial authorization. Earlier v0.57 unconditional no-launch gate remains in force. **Actual model trials=0; paid model calls=0.**

## 5. Frozen evidence, tests and reproducibility

Additive v0.59 source-only files:
- `tools/bibimbap_v059_topo18_native.py` — original SHA-pinned source geometry projection, full/compact complete-state parsing/reconstruction, real IFC mutation, **independent** source-native IFC semantic/relationship/schema oracle.
- `tools/bibimbap_v059_topo18_sessions.py` — genuine D full, D complete-managed and pinned Linux Docker Python I model-facing sessions, identical initial source read, 25 total tool calls, atomic last-good native IFC promotion.
- `tools/audit_bibimbap_v059_first_holdout_native_DI.py` — source-only geometry contact classification, 9 real IFC cases, 3 real Linux Docker Python runs, separate pinned original author evaluator-side grades, adversarial real Docker/rollback replay and six-task fixed shortlist status.
- `tests/test_bibimbap_v059_first_holdout_native_DI.py` — **57 focused tests**, including source six-wall geometry, D final-state completeness, unexpected IFC entity change/relation/metadata violations, DTD/XXE, no-op, unmanaged GUID, malformed XML, 25-call cap, fail-closed missing Docker and source hash, rollback, direct native source schema delta, and no author-grader/GT/provider import.
- `reports/bibimbap_v059_first_new_source_native_topo18_20261118.json` — immutable source/IFC hash and original author *evaluator-side* Boolean metric results; no original question text, private answer target GUID or worker code committed.
- This methods protocol.

**Frozen v0.59 report SHA-256: `a40d236129d39014b9127619fd5b63fca5b19eaf3f967027e2ee1338ac6af4ec`**.
**Frozen v0.58 parent report SHA-256: `0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8`**.

In the independent Windows research worktree with original local source/data and pinned Linux Docker runtime:

    python -m tools.audit_bibimbap_v059_first_holdout_native_DI --check
    python -m unittest -q tests.test_bibimbap_v059_first_holdout_native_DI

`--check` truly reruns the 9 original source IFC candidates through genuine D + genuine OS-isolated Docker I, 9 evaluator-only author-module executions, adversarial Docker commit refusal and last-good rollback, and compares canonical report bytes exactly. If Docker/IFC source is unavailable or any SHA drifts, audit fails, never falls back to an offline fake. `--write` is exclusive-create and never overwrites prior reports. This is a valid **one-task native engineering implementation**, not a launchable six-task causal benchmark.
