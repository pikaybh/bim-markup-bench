# BIBIMBAP v0.40 — P2 original native IfcSpace read-only evidence in model-facing whole XML

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/195
**Stacked parent:** v0.39 [Draft PR #194](https://github.com/pikaybh/bim-markup-bench/pull/194), frozen head `071c97b380b5a25821aff5b41e071cb33a1daf93`
**Authoritative final frozen machine report (native-mm exact indexed mesh):** `reports/bibimbap_v040_original_p2_room_native_mm_exact_20261117.json`, SHA256 **`8f5a9d8df436e52139a09c6fd78a961d71684303eb8499d8d61513adca305f3e`**. **Preserved preliminary report (superseded, not valid for exact indexed source mesh claims):** `reports/bibimbap_v040_original_p2_room_readonly_xml_live_20261117.json`, SHA256 **`20dfa8000f2f8198eaedfa2a53ecbaa8e55b31981a5cba7c4ef85741aaa9daf0`**. The earlier report is not rewritten or deleted.

## Evidence and research boundary

This is an original-public task-sourced, **developer-authored, nonblinded, non-LLM** experimental writer/read gate for two previously demonstrated P2 original CREATE cases. Both were admitted by the future matched-model XML session, but their real IFC4X3 `IfcSpace` source objects were **not** exposed in its editable source XML. This is separate from the 5/15 earlier **task-specific** original CREATE D0/I0 native semantic controls, and does **not** increase that count or prove a successful answer to either original task.

The immutable original BIBIMBAP 45 population stays 45 (=15 CREATE +15 UPDATE +15 DELETE), with all 10 other original CREATE tasks still lacking independently developed **task-specific** D0/I0 output witnesses. The original author and data Git SHAs, original public question SHA values and native source file bytes are pinned against the previous v0.37 and v0.39 frozen reports. Neither original scorer nor hidden GT was read or changed.

Before writing any new implementation, independently reopened original native IF4X3-mm IFCs and confirmed these source-only facts:

| Original public task | Native source SHA256 | Original named GUID and literal native IFC class | True native IfcSpaces |
| --- | --- | --- | --- |
| `topological_test_01` — wall enclosing a named room | `2cb6cc753784c13fcd1f6f037b97431294cc3c91db9bcc75213ba61b8e3a18ac` | `3_DHXxtdb3wRKlXgyMiH4s` **is IfcSpace** | **1** room, 8 vertices / 12 triangles, bbox (0.2,0.2,0)–(4.85,6.2,2.7)m |
| `topological_test_03` — wall separating two alleged “rooms” | `1035e999dd8579b7d2c33950498eea1f50bd9ff81e1816bdf4b9893901969466` | Both `0rMMWWDi1E0Qbe7dlPjRaK` and `0rMMWWDi1E0Qbe7dlPjRcx` **are IfcWall, not IfcSpace** | **2 distinct** native rooms (`0rMMWWDi1E0Qbe7dlPjRlq`, `0rMMWWDi1E0Qbe7dlPjRlx`), each 12 vertices / 20 triangles |

All three real source IfcSpaces are spatially **aggregated to original Storey** (via actual native `IfcRelAggregates`), not separately contained via an inferred `IfcRelContainedInSpatialStructure`. Both files have **exactly zero explicit `IfcRelSpaceBoundary` records**, even though the rooms have physical native shapes. We do not infer adjacency, enclosure or space boundaries from visual geometry, assign the wrong public wall IDs to the separate native spaces, or relabel the original author questions/evaluator.

## Source-faithful opt-in representation, not fake editable Rooms

The new **opt-in only** `XmlSourceEditSession(..., experimental_original_room_v040=True)` opens exactly the **two** SHA-pinned original source files with their real IFC4X3 schema and native millimetre units. The v0.38 legacy and v0.39 complex source experimental switches are mutually exclusive with v0.40. Without opt-in, the exact previous default typed XML host remains in use: it continues admitting these two original sources **without source-native IfcSpaces visible**, the known v0.37 P2 blocker.

The separate new schema `spec/toy_markup_native_room_evidence_v040.xsd` copies the old validated Wall authoring schema without changing `spec/toy_markup_v0.xsd`. It appends exactly one `OriginalNativeRoomEvidence` child after `Relations` in the model-facing **complete declarative Building XML document**. The new immutable section includes:

- Every native source IfcSpace with **literal original GUID**, `IfcSpace` class, Name, LongName, exact source Storey aggregate GUID, true 3D world vertex/triangle mesh (not an axis-aligned replacement cuboid), world envelope, original mesh digest and absence of explicit room boundaries.
- Every verified **explicit original IFC Space-to-Storey aggregate relation**; zero fake `IfcRelSpaceBoundary`, and no conjectured wall contact or inferred adjacency graph.
- Every room-like **public question identifier** with its real native IFC class and a clear `PUBLIC_ROOM_NOUN_NATIVE_SPACE_MATCH` or `PUBLIC_ROOM_NOUN_NATIVE_WALL_MISMATCH` classification. `remappingOrInferredRoomGuidAllowed=false` is enforced; the two actual IfcWall GUIDs remain the question’s original literal GUIDs.

All attributes and mesh vertices, triangle indices, relationship evidence and public GUID classifications in `OriginalNativeRoomEvidence` are **immutable**. The new trusted host validates the separate v0.40 XSD, source/original SHA and the original native reference subtree's canonical XML representation *against an independently reconstructed original source projection* for each submit. It strips **only** this verified read-only reference subtree and sends the remaining complete typed Wall XML to the preexisting trusted external `compile_declarative_xml` v0.1 compiler. The XML model **cannot** edit source IFC Space geometry or use these native references as imperative IFC APIs. The model tool surface remains only `read_building_xml` and `submit_building_xml`; the future paid model trial CLI has **not** automatically enabled v0.40.

## Actual native source + writer evidence

Both original IFC files were opened in unique disposable local Worktree scratch sessions, first through the unchanged default XML host (confirming the original source Room omission), then through the new v0.40 opt-in. For both opt-in sessions, the model-facing complete XML read included all native source IfcSpaces and classified public GUIDs as above.

After source read, the developer submitted **one demonstrative generic Wall** at x1=8,y1=0,z1=0 to x2=9,y2=0,z2=0, height 2.5m, thickness 0.2m. This was intentionally *outside* the task-relevant original room area, is **not** a completed enclosure/separation answer, and is not original-author graded.

Both actual `submit_building_xml` calls returned committed native IFC4X3 candidates, restored to the original native millimetre units. A **separate source/output IFC oracle**, independent of the v0.40 compiler module, verifies actual saved native geometry/relationships:

| Native physical criterion | `topological_test_01` | `topological_test_03` |
| --- | --- | --- |
| All original source IfcRoot GUID/class/Name/Description preserved | **88** | **112** |
| All original source IfcProducts preserved | **10** | **13** |
| Exact source IfcSpace identities, geometry, Storey aggregation preserved | **1** | **2** |
| Non-new source shaped products’ physical world mesh checked | **6** / 72 triangles | **9** / 124 triangles |
| Original and output explicit IfcRelSpaceBoundary count | **0 / 0** | **0 / 0** |
| One physical native new IfcWall and original Storey containment | PASS | PASS |
| New Wall native world bbox metres | (8,0,0)–(9,0.2,2.5) | Same |
| Original public source IFC byte-SHA after all tool calls | Unchanged | Unchanged |

The oracle verified that the actual native Wall thickness is a **one-sided offset from its source axis**, not a centered +/-thickness/2 representation. The initial stricter assumed bbox check was corrected only after inspecting an independently saved native source-derived Wall; no original scorer, original test, original question, or frozen evidence was changed.

No original `IfcSpace` source geometry or relation was changed. The source IFC4X3 unit system is restored after the trusted native compile. All original Root identities and existing explicit IFC topology edges are preserved, and no invented room boundary appeared. This is **not** entire IFC STEP entity-by-entity or byte-for-byte preservation, complete model-visible source equality, or native write-permission parity against a matched independent Python arm. Generated candidate whole-file SHA values are not treated as canonical equal outcomes across model arms.


### Post-preliminary independent native-mm mesh forensics (material correction)

After the preliminary 43-test report was frozen, an **additional independent original native-mm IFC-to-model-visible XML indexed-triangle audit** discovered that IfcOpenShell's IFC native-millimetres → working-metres conversion **retessellates one of the two 20-triangle IfcSpace source meshes** in `topological_test_03` (original IfcSpace `0rMMWWDi1E0Qbe7dlPjRlq`): physical world vertex positions and planar surface areas remain unchanged, but its triangle index triples/face diagonals differ. The other original IfcSpace `0rMMWWDi1E0Qbe7dlPjRlx` has unchanged canonical triangle vertices. The initial v0.40 projector incorrectly treated the normalized working clone as the definitive source for original indexed mesh faces. This did **not** change original IFC objects or physical geometric validity, but did invalidate a claim of exact original indexed-triangle fidelity. Merely calling the triangles physically equivalent would not satisfy this separate source-representation precision requirement.

The experimental projector and its model-facing host now explicitly require the **immutable, exact SHA-pinned original native-mm file** as an additional trusted input. **The original mm IFC, not the normalized converted clone, owns the space mesh vertex coordinates, exact indexed face triples, original Storey aggregate relations, and published named GUID classes.** The normalized IFC still owns the legacy v0.1 typed Wall authoring workbench. A separate **implementation-independent audit** reopens original native-mm source, retains the IfcOpenShell generated shape's memory owner, and requires **each original IfcSpace vertex in its source order within 0.5 micrometres and EVERY indexed triangle face triple exactly equal** to the model-visible read-only room XML. Any different diagonal now fails rather than being silently presented as the original source.

Rather than rewriting the earlier frozen report, the preliminary `20dfa800…` evidence is retained as a labeled, **superseded v0.40 pre-forensic observation**. The **new final `8f5a9d8d…` report** is exclusively created as a distinct filename, with per-room `read_only_XML_indexed_mesh_matches_original_native_mm_IFC_exactly=true` and an explicit top-level source index-fidelity gate. It supersedes only the preliminary v0.40 projection claim; v0.31–v0.39 evidence, all original 45 tasks, original source IFCs, published evaluator and hidden GT remain unchanged. This additional check still does **not** prove full original IFC STEP or IFC metadata parity.

## Integrity and security negative gates

Tests use actual original IFC files, source SHA and question SHA gating, external XSD, original native mesh facts, exclusive report writer, and real tool calls. Wrong original source, same-schema tampered copy, unit-altered source, opt-in conflicts, forged native `IfcSpace` GUID, Storey aggregate, mesh digest or triangle, fake `IfcRelSpaceBoundary`, rewritten public IFC class/room identifier, removed evidence, forged source model hash, DTD/XXE, new typed Space, multiple new Walls and edited original Wall are rejected. A failed second edit must preserve the prior valid XML and native IFC. A separately mutated native IFC with a relocated original room or missing new Wall physical representation fails the independent oracle.

Frozen P2 audit: `tools/audit_bibimbap_v040_original_room_live_host.py` (reexecutes both real original host inputs, checks all 45 public tasks, prior frozen reports and native oracle); source facts `src/runtime/experimental_v40_native_room_evidence.py`; independent native oracle `tools/bibimbap_v040_native_room_oracle.py`; focused tests `tests/test_bibimbap_v040_original_room_live_host.py`. No compiled IFC, hidden GT or paid model response is committed.

### Reproduce locally

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v040_original_room_live_host --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
& $py -m unittest -q tests.test_bibimbap_v040_original_room_live_host
```

The `--write NEW_UNUSED_PATH` audit option creates a new report **exclusively with `xb`**; it never overwrites earlier frozen evidence. The preliminary v0.40 focused suite passed **43/43** in 6.433s *before* the additional source-index audit and is preserved separately. The final corrected source-native-mm/index-exact implementation passed **45/45 focused tests in 6.990s, process exit 0**; local ignored log `results/v040_native_mm_exact_focused_20261117.log`. The **selected 24-module multi-version non-Docker regression** for the final corrected implementation passed **561 tests: 557 PASS / 4 SKIP / 0 FAIL**, **246.620s, process exit 0**; ignored local log `results/v040_native_mm_exact_selected_nondocker_regression_20261117.log`. It includes v0.38 and v0.39 compatible suites, previous original D0/I0 developer controls, and 45 source-exact v0.40 tests. This is **not** whole-repository validation, Docker worker isolation, or matched real LLM evaluation. Historical v0.37 tests freezing the *old host's source code SHA* remain valid in their own frozen v0.37 worktree, not against this deliberately revised host. The old v0.37 code-identity-frozen host test remains assessed in its own old worktree, not spuriously claimed as passing when the host source has changed.

## Scientific conclusion and next work

**P2 source visibility gap addressed for these two original sources only**: one originally named true IfcSpace and two other true native spaces are now visible as read-only source evidence, and the room-word-vs-IfcWall discrepancy of both public GUIDs is explicitly disclosed. There is **no claim that the problem statement's native-semantic inconsistency has been repaired**; the correct interpretation of the published `topological_test_03` instruction remains an explicit experimental ambiguity to preregister before any scored model run.

**0/45 complete equal-facts model-visible source parity proven, 0/45 complete equal-write native D/I capability proven, 0 original task-specific scores in v0.40, 0 real matched LLM D/I experiments and 0 new paid model calls.** A generic Wall writer probe is not original task completion. The future matched LLM trial CLI remains opt-in disabled.

The next work is **P3**: real model-facing whole-XML generic Column/Slab CREATE for `geometry_test_02`, `topological_test_02`, `topological_test_04`, with separately verified physical shape and source preservation. Then verify complete equal-information and equal-write-capability conditions and run statistically sufficient independent matched LLM D vs I trials before making a causal performance claim.
