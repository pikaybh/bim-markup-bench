# v0.66 / Issue #247 — source-neutral Window assembly MOVE/DELETE, two exposed IFC sources

**Status:** Verified offline developer-engineering control, additive to research-only Draft PR #248 stacked on v0.65 Draft PR #246. This is NOT blinded matched LLM evidence, a published scorer result, or evidence of XML superiority. No BIXML/Xim product code or prior Frozen Contract/report changed.

## Direct final-state XML, not a command bus

The new tool module tools/bibimbap_v066_window_final_state.py has **no task ID, fixed original IFC SHA, answer GUID, author task scorer, model-facing operation invocation or private GT**. It expects the immutable source SHA and IFC4X3/millimetre original IFC, derives Window+hosted Opening+unambiguously assigned physical detail-proxy groups from native IFC relations and geometry, then emits either:

- D_FULL: a complete source-anchored BuildingState XML with all original source product identities, world extents and source-opaque provenance, plus every managed element.
- D_MANAGED: the **entire** stable-ID managed roster with an SHA256 binding to exactly the full source state.

Each original Window, Opening and affiliated proxy is an Element with ifcGuid, ifcClass, present=true|false, finalWorldMinXM, finalWorldMinYM, finalWorldMinZM. There are NO XML Move, Delete, Create, Update or Set operation instructions.

A trusted runtime infers from comparing source and final state exactly one changed group:

- Move: all Window+Opening+details remain, and all final world XYZ coordinates shift by the same horizontal vector, 1 cm–1 m, no Z motion. Move Opening and exclusive detail-placement native points by source parent transforms; Window inherits Opening. Original source geometry and Root identity persist.
- Delete: all group members are absent and their coordinates remain unchanged. Native IfcOpenShell root.remove_product removes detail members, Window, Opening and linked hosted relationships.

Parser refuses no-ops, partial/mixed edits, multiple changed groups, missing/reordered rows, altered original provenance, source SHA/units drift, DTD/XXE, illegal Z shifts, shared placement and ambiguous detail groups. It is intentionally NOT a universal editor.

## Independent native IFC scope and fairness

tools/bibimbap_v066_window_native_scope.py derives the changed group **from two native IFC files, not from the edited XML, task question or author answer**. It builds a separate API replay reference for the observed move or deletion. It independently checks all original surviving Root GUIDs/classes and product/relationship roster, full typed native IFC entity/attribute/reference multiset graph at 0,1,2,4,8,16 refinement depths, and true reopened world-geometry bounding boxes. It compares physical outcome against an independently recreated reference and rejects new IFC schema findings.

The graph fingerprint never includes arbitrary STEP entity numbers. Numeric IFC millimetres are normalized to 6 decimal places (1 nm in physical world) to permit harmless writer roundtrips; **only** explicitly recognized EXPRESS SET-valued attributes are sorted as unordered. Native API cleanup may update OwnerHistory.LastModifiedDate; a 300-second bounded expected/candidate clock skew is tolerated, not other metadata changes.

**Scientific limitation:** This is a restricted independent *source-native API replay* oracle, not full IFC graph semantic isomorphism or official benchmark scorer. A lawful native representation rewrite outside this source-authoring family may be falsely rejected; this limitation is preserved, not hidden.

## Actual real native IFC evidence

Only **two previously developer-exposed IFC4X3/millimetre** original source SHA clusters were used. Task IDs are restricted to the offline audit harness, never the source-neutral compiler/validator.

| Exposed original source (audit metadata only) | Native Window groups | Selected group members | Move D_FULL / D_MANAGED / pinned Docker Python I | Delete D_FULL / D_MANAGED / pinned Docker Python I | Native illegal candidates rejected |
| --- | ---: | ---: | --- | --- | ---: |
| geometry_test_13 | 2 | 5 (Window, Opening, 3 details) | 3/3 PASS | 3/3 PASS | 4/4 |
| geometry_test_19 | 7 | 2 (Window, Opening) | 3/3 PASS | 3/3 PASS | 4/4 |
| **Total** | | | **6/6 PASS** | **6/6 PASS** | **8/8** |

Local developer control: choose the first original Window under GUID sorting; move it 0.2 metre along its host Wall's major horizontal world axis. This is source-native, NOT an original task target or hidden-answer selection. D_FULL, D_MANAGED and independently authored generic Python/IfcOpenShell in genuinely isolated SHA-pinned Linux Docker each produced actual native IFCs with identical bounded physical edit semantic digest per case. A total of **12** actual independent native D/I results plus **4** additional legal native IFC variants with every STEP numeric entity label and reference bijectively changed (16 legal IFC admissions), and **8** negative IFC mutations passed/fail-closed appropriately. The four reindexed variants contain 1,048 / 986 / 786 / 762 STEP entities respectively for the two move/deletes. Their semantic edit digests match all three D/I outputs exactly.

Native negative fixtures include existing unrelated Wall metadata tamper (all 4 cases), incomplete detail-proxy synchronization, unreferenced extra anonymous IFC entity and unauthorized second Window deletion. Parser negative tests cover operation-style markup and partial/mixed/unsafe state.

**Frozen JSON report:** reports/bibimbap_v066_window_move_delete_native_20261118.json

**SHA256:** b7ee995579d32a887dc5a34882950f2b967861b27e132591b7dd8fab40b7c8be.

## Offline reproduction

Use the existing source-copyright-blocked but local and already developer-exposed research environment; no paid/remote provider or new original IFC acquisition.

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_window_final_state --check
    & $py -m unittest -q tests.test_bibimbap_v066_window_final_state
    & $py -m tools.audit_bibimbap_v066_native_semantic_admission --check
    & $py -m tools.audit_bibimbap_v065_offline_generalization --check

The audit runs fresh real D/managed XML to native IFC compilation and four real independent isolated pinned Linux Docker Python edits, native source/physical verification and negative IFCs; it recomputes the JSON byte-for-byte. It DOES NOT access original private graders, hidden target, any genuinely unseen sources or model/provider calls.

## Remaining research limits and next priority

The two edit sources are both IFC4X3; IFC2X3 Window moves/deletes, alternative legal native representations, curved walls, shared placements, complex multi-object transformations and unknown source geometries remain UNSUPPORTED. The candidate grammar is *partial IFC-backed state* with an opaque source pass-through, NOT lossless stand-alone BIM source. This engineering success is **not an LLM agent success rate** and cannot support a causal XML-vs-Python conclusion. Original pinned author scorer/paper revision parity remains unverified, 31/31 original per-IFC rights/provider transfers blocked and independently certified blind source families ZERO.

Next: freeze prospective matched D_FULL/D_MANAGED/I Python tool-read-feedback/bytes/token budget using these exposed sources OFFLINE, without conflating proxy token estimates with billed tokens, and independently verify original-data rights/official scorer before any trial authorization. Do not merge, change original scorer/frozen reports, launch a paid model or upload copyrighted IFC.
