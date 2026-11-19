# BIBIMBAP v0.66 / Issue #247 — synthetic IFC4 Window–Opening move/delete native D/I parity

**Status:** Actual **local native IFC4 engineering test**. NOT GNI IFC data or model task success, NOT a genuinely blind evaluation, NOT a published BIBIMBAP evaluator score, NOT a rights/license or provider approval.

## Purpose and strict boundary

The public GNI BIM Dataset describes IFC2X3/IFC4 source families. The original v0.66 source-neutral Window final-state tool supports IFC4X3/mm only. The prior synthetic IFC4 checkpoint proved a bounded hosted Door **create**, but did not test moving/deleting hosted Windows. This extension uses **four NEW self-authored IFC4 source models only**: native metre vs millimetre, and represented wall X vs Y orientations. Each source has two separately hosted Window+Opening assemblies on one 6-m wall, preserving an unrelated slab. No actual GNI ZIP/IFC download, original 31 BIBIMBAP source IFC access, hidden grader/GT, paid or free LLM, uploader, or authorial scorer access occurred.

The **source-independent XML editing boundary** is the stable identity roster of every original Window+Opening; the rest of the native IFC is immutable opaque input. D_FULL exposes a complete BuildingState with source product metadata/meshes; D_MANAGED exposes a SHA-linked complete managed final-state roster. The editor alters only final physical presence or final world-coordinate values; the trusted compiler outside the LLM loop diffs source and submitted complete state and derives a bounded edit (one move OR one deletion). **The XML has no <Move>, <Delete>, <Update> or pseudo-imperative command tags.**

Implementation files:
- tools/bibimbap_v066_ifc4_window_synthetic_host.py — deterministic IFC4 source: two Window/Openings with a real child-placement dependency, X/Y walls, m/mm lengths and source-aligned GUIDs/IFC SET order
- tools/bibimbap_v066_ifc4_window_final_state.py — isolated IFC4-compatible extension of prior IFC4X3 D_FULL and D_MANAGED complete-source final physical roster, trusted native compiler
- tools/bibimbap_v066_ifc4_window_native_scope.py — isolated IFC4-compatible exact source/no-STEP-number dependency native scope checker. Conservative IFCSOURCE API replay oracle; NOT universal IFC graph isomorphism
- tools/audit_bibimbap_v066_synthetic_ifc4_window_DI.py — genuine paired D_FULL/D_MANAGED vs independent general IfcOpenShell Python in SHA-pinned local Linux Docker; no D compiler imported by I; 1 own-source Window group edited per case
- tests/test_bibimbap_v066_synthetic_ifc4_window_DI.py — **60 new tests**
- reports/bibimbap_v066_synthetic_ifc4_window_DI_20261119.json — reproducible canonical proof, source-generator/grammar/native-scope file SHA frozen

**Frozen report SHA256:** 4d95bb260cd8203bf282b2a5fb7293760aa356ff9a234584f34d5324fdc02300

The original IFC4X3 Window modules and all pre-existing Frozen reports remain unchanged; existing v0.66 prompt/session/model trial rights gates remain blocked.

## Actual executed results

| Synthetic IFC4 source scenario | Native move D_FULL/D_MANAGED/I | Native delete D_FULL/D_MANAGED/I | Source independent root class/metadata preservation |
| --- | --- | --- | --- |
| metre / X wall | PASS / PASS / PASS | PASS / PASS / PASS | PASS |
| metre / Y wall | PASS / PASS / PASS | PASS / PASS / PASS | PASS |
| millimetre / X wall | PASS / PASS / PASS | PASS / PASS / PASS | PASS |
| millimetre / Y wall | PASS / PASS / PASS | PASS / PASS / PASS | PASS |

**4 synthetic IFC4 sources × 2 operation families × 3 arms = 24 actual native outputs**, each admitted by a separate graph/physical edit oracle and producing matching source-scoped semantic digest across all three arms (for the same source/operation). Native Python runs genuinely in the existing SHA-pinned Docker interpreter and uses the original project's actual LENGTHUNIT conversion, not a forced millimetre assumption. Window inherits its Opening placement; moving one Opening by **0.25 metres along the source wall** moves both; deleting one Window+Opening removes corresponding fills/voids relations and preserves the other assembly. The opaque original Slab remains unchanged.

Additional genuine native controls:
- **8 physical STEP-renumbered variants PASS**; numeric STEP entity identifiers are not semantic identity.
- **32 bad final XML candidate controls rejected**: forged source SHA, incomplete managed roster, fabricated XML operation element and incoherent movement/deletion of only part of a Window–Opening group.
- **24 mutated native IFC outputs rejected**: unrelated original Wall metadata change, unreferenced anonymous Cartesian point, or an extra unauthorized alteration of the surviving Window group.
- Each native source SHA survives all D/I arm executions unchanged; no new IFC schema errors.

### Frozen synthetic IFC4 original-source SHA256

| Unit + wall axis | Source SHA256 |
| --- | --- |
| metre-X | fc932427e54f5740b879fc17c382963b2188175c9031843a0f107173328b428a |
| metre-Y | c1bbfe9000174ddaa97bc1c15bcb70a2182aac26e070569986635a3e6b4ab020 |
| millimetre-X | 370e83184cfb69a9430a021ece1bf069673d0e1b5118eae1a7cbc69bb77eb6f8 |
| millimetre-Y | cc4742e8e65ad36ffe480ad119da09f30fa68ca2b823c68e59bbdf45126b191a |

Each input is generated from project-authored code and an existing synthetic host, not stored in the Git report as raw IFC. Deterministic native SET ordering and GUID creation make source SHAs and final report reproducible across independent runs.

## Limits / what remains

This tests **only simple hosted Window+Opening assemblies with exclusive local placements**, two original windows, no detail proxies, no shared placements, no multi-window edit or curved/multi-segment curtain-wall boundary. IFC2X3 Window move/delete remains **unverified**. GNI source model complexity/actual IFC4 geometry support and per-member rights remain **unverified**, as do paper-scorer equivalence and independent evaluator task blindness. Oracle parity with a narrowly defined source API edit path does not prove equivalent legality of every native IFC authoring strategy. Three-arm output equality for developer-authored controls proves plumbing, not causally superior LLM reasoning for XML.

**No new model-generated attempts, no external IFC transfer, no original author or GNI IFC download, no hidden GT.** The independently blind cohort is still **zero**, per-source rights/retention are not approved, and published paper evaluator release SHA/tag equivalence is not proven. Do not promote Draft PR #248 or Issue #247 to closed/merged status or authorize trial solely because this native technical test passes.

Next priority after IFC4 Window technical compatibility: independent source steward rights-verified *specific individual IFC acquisition*, actual external task/evaluator preparation and publisher scorer release-crosswalk; only then owner-approved model/tool/token/budget preregistration. Until that process, limited synthetic hardening is the only evidence of additional coverage.

## Offline replay

Run from the research worktree with the existing trusted local IfcOpenShell Python venv and Docker sandbox:

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_synthetic_ifc4_window_DI --check
    & $py -m unittest -q tests.test_bibimbap_v066_synthetic_ifc4_window_DI

The audit independently synthesizes/reopens four IFC4 source files, executes 24 actual native D/I outputs, validates eight real STEP relabelled IFC alternatives and rejects 56 real malformed XML/native IFC candidates. The check compares canonical output against the frozen report **byte-for-byte**. It requires actual pinned local Docker for I; it does not simulate or automatically invoke any provider, source acquisition, grader or model.
