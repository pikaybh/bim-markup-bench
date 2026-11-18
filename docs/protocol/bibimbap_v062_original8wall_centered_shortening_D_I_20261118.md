# v0.62 — Original IFC4X3 eight-Wall centered shortening, native D-state versus actual Docker I

**Research:** BIBIMBAP original-public-source editing benchmark, independent repository `pikaybh/bim-markup-bench`, [Issue #239](https://github.com/pikaybh/bim-markup-bench/issues/239).
**Stacked parent:** v0.61 [Draft PR #238](https://github.com/pikaybh/bim-markup-bench/pull/238), source HEAD `fb59e9e113a0e0f0709e8d2ede8569f023e243b3`.
**Scope:** ADDITIVE separate worktree. Original source IFC, original author scorer, original questions, existing main, prior frozen reports, stash and Xim/BIXML product are not edited. No model provider calls/uploads.

## 1. Original source/topology, exact supported edit

Original public task `topological_test_12`: “Shorten the length of the wall by 1m that is outside of the walls with [six original source Wall IDs].” Exact original native IFC4X3 source SHA-256 `1f10c164d5ba6ffad7a22ce5d4e5f869b81abe497463c3ef0c3262c0a679ec83`, relative public original source `01/02/01_02_012.ifc`. Its unmodified source contains **eight IfcWall**, **seven original IfcRelConnectsPathElements**, two Slabs, two Columns, one Space. Six public-question named Walls form the connected outside perimeter. Two are excluded from that six; one excluded Wall is connected to another Wall, while the other is a standalone **2.0m-long source IfcExtrudedAreaSolid RectangleProfileDef** (source representation Axis Curve2D plus Body SweptSolid). The seven other Walls have source BooleanClippingResult bodies, some with original path joins. The one standalone Wall has no path joins, and source body is width 200mm, height 2700mm.

**Actual original IFC native length units are millimetres; IfcOpenShell world mesh coordinates are metres.** The physically requested shortening is from 2000mm to 1000mm. Wall ObjectPlacement and source native original centre must remain fixed, and the wall axis and Body profile must remain geometrically consistent. Source Axis local start point is SHARED with multiple other IFC elements: **never mutate this shared point directly**, even if the edited Wall output looks plausible.

This native representation subset is intentionally conservative. It supports only the source's **one unique unconnected SweptSolid Wall**, NOT arbitrary connected, clipped Walls. The source-only eligibility rule and model-facing representation **make the intended Wall relatively easy to identify** and can leak task-selection information. This is an important experimental confound: no fair causal D-versus-I conclusion follows from engineering acceptance here. A different IFC authoring approach using an alternate valid representation/STEP relabeling may be semantically valid but still rejected by this source-specific oracle.

## 2. Center-preserving IFC geometry implementation

The genuine source/geometry-preserving solution needs **ONE new IfcCartesianPoint and exactly THREE changes to original native IFC entities**:

1. Create a new unique native CartesianPoint for the selected Wall Axis start at original profile-centre minus half the new length, **500mm** along local X. The source Wall's shared original Axis start CartesianPoint stays unchanged.
2. Rewire only that Wall's original Axis IfcPolyline point list to the new point and its pre-existing unique original end point.
3. Move the original unique Axis endpoint to local **1500mm** and set the original unique RectangleProfileDef XDim to **1000mm**. Keep rectangle centre at its original local X **1000mm**, Y=0; keep Wall ObjectPlacement and parent structure unchanged.

Thus the Axis goes from local [0,2000]mm to [500,1500]mm and the Body rectangle remains centered at X=1000mm while reducing from 2000mm to 1000mm. Actual reopened world mesh has its original **world-Y centre unchanged**, both source world-Y endpoints move inward by exactly **0.5m**, original thickness, Z span, other native geometry and seven path joins remain unchanged. The original shared source point and every other source entity remain untouched. The original source-versus-output IFC4X3 schema-validator delta must add **zero new findings**.

**Important scorer provenance finding:** An initial valid physical shorten preserving the world START rather than CENTER yielded only **2/3 in the pinned original author repository evaluator**: dimensions/integrity true but `right_location=false`. We then examined the unmodified author evaluator's checks; it explicitly expects the original Wall world bbox centre and placement to remain unchanged. A source-native centered and symmetric shortened edit yields **3/3**. Thus the developer-control implementation was informed by the pinned evaluator's observed expectation. This is **developer/benchmark information exposure**, not a blind independent held-out model trial. The report records the difference and does not conceal it.

## 3. True declarative final-state D, managed D, isolated Python I

All three model-facing sessions start by reading the **same exact original source-anchored `BuildingState` XML of 5,287 UTF-8 bytes**. The source subtree includes the SHA-pinned native IFC4X3/mm source product/root identities, original world-metre physical bbox, original Wall Axis lengths, source Body representation types and original path connection counts.

- **D_COMPLETE_XML_V062:** model returns the **entire** immutable original `BuildingState` XML plus all **eight source Wall GUIDs** in the explicit complete managed final-state roster, each with **absolute final `finalAxisLengthM`**. The input describes a final physical condition, not an editing operation, typed `NativeEditPlan`, AST, diff, omitted row or Python command. The full source product/geometry/connection subtree must be byte-canonical-unchanged.
- **D_MANAGED_FINAL_STATE_V062:** model submits an **entire eight-Wall managed final-state roster** (initial compact XML **955 UTF-8 bytes**) anchored to both original IFC source SHA and full original source `BuildingState` SHA. The trusted source-only host reconstructs the complete original source XML and validates it using the same D_FULL validator before emitting actual native IFC. No missing-row backfill, instruction opcodes or partial subset.
- **I_NATIVE_DOCKER_V062:** actual arbitrary Python/IfcOpenShell code executes on cloned original IFC4X3 with explicit `commit()` in the real source-attested pinned OS-isolated Linux Docker worker. Nonroot, network-none, read-only root, dropped Linux capabilities, bounded mount/image/CPU/memory/processes, and native success/rollback attestation are retained from the previous checkpoints.

All arms have **25 total tool calls** and identical initial original-source read XML. However editing affordances are **NOT** controlled equivalents, model output length differs (5,287 vs 955-byte initial state), and after edits D read returns updated complete XML while I repeat read is original source XML. No actual provider token/billed USD, decoding/context balance or ITT measure exists yet. This is implementation readiness, NOT a causal matched LLM experiment.

## 4. Independent native source/IFC scope oracle

The source-only native oracle admits a new candidate IFC only if:

- Original source SHA unchanged; candidate distinct regular IFC4X3; all original STEP IDs, original Root identities, native attributes and all source material/relationship/other physical product geometry remain, with no unexpected deletion.
- **Exactly ONE NEW** independent IfcCartesianPoint, referenced by exactly one modified original standalone Wall Axis; source shared start point is not changed; exactly THREE original entities change: selected Axis IfcPolyline's point references, its original unique Axis end CartesianPoint coordinates, and original single RectangleProfileDef XDim.
- The new start and existing end straddle the original rectangle profile centre symmetrically; no original Body centre or ObjectPlacement change; candidate's actual reopened world mesh physically contracts by the original length minus new length **equally from both ends**, without changing world centre, wall thickness or Z extent. Other eight-wall relationships and the existing seven path connections are preserved.
- Original-source vs native candidate IFC4X3 schema-error multiset adds **zero new errors**; both original input and candidate SHA remain stable throughout validation.

The oracle **does not know the public question's required exact 1m reduction or original author target answer**, and admits bounded shorter lengths like 0.5m or 1.5m as structurally safe variants. The public question's correctness is an independent evaluator-only physical layer, separate from original author repository metrics. The strict source-specific STEP representation can reject alternative physically valid edits and is not universal IFC equivalence, Revit parity or general Wall editing.

## 5. Real developer controls and original author repository score

In an isolated actual original IFC engineering audit, three source-only developer control cases were run via **all three execution arms**, creating actual native IFCs from the pinned unmodified source:

| Source-only developer control (final length) | Native IFC D-full / D-managed / real Docker I | Original repository grader mean |
| --- | --- | ---: |
| **2.0m → 1.0m** centered (correct 1m shortening) | 3/3 PASS | **1.00** |
| **2.0m → 1.5m** centered (wrong 0.5m shortening) | 3/3 PASS | 0.666667 |
| **2.0m → 0.5m** centered (wrong 1.5m shortening) | 3/3 PASS | 0.666667 |

**9/9 actual native IFCs accepted; 3/3 genuine pinned Linux Docker Python executions; original source and all non-target native entities unchanged; zero new source IFC schema findings; canonical semantic IFC digest matches across D/M/I for each source-only developer case.** Original author `data/tests/topological_test_12.py` `execute_test` was imported and called **only inside a separate evaluator-side audit**. For the correct native task it returns `right_dimensions=true`, `right_location=true`, `integrity_constraint=true`. The two wrong length cases fail `right_dimensions` but preserve location/integrity. These are **repository evaluator scores**, NOT official published paper scorer-equivalence verified, NOT generated LLM scores or published comparison results.

Actual Docker adversarial check (a real Python script that edits only the Wall Axis end without matching Body/profile) was rejected with no native commit. Another actual isolated Docker session committed a valid centered source Wall shorten then tried to change unrelated clipped Wall metadata; independent native oracle rejected the second candidate and preserved the previous native IFC bytes SHA-identically. A D_FULL good commit followed by malformed/incomplete eight-Wall final-state XML likewise preserved last-good native IFC and accepted XML unchanged.

## 6. Freezing, reproducibility, research constraints

Six strictly additive research-only files: source original Wall full/compact declarative XML compiler + native geometry/STEP/schema oracle; genuine local Docker I and two D sessions; evaluator-only real source native IFC author repository scorer/actual Docker replay audit; **84 focused original-source security/semantic tests**; immutable report; this methodological protocol.

- Frozen v0.62 report `reports/bibimbap_v062_original8wall_centered_shortening_native_DI_20261118.json` SHA-256 **`c80b6d4c6b39c51eaac96177515f0f6cd93f36e37298bae973ae4f7e57c11842`**.
- Frozen v0.61 parent report SHA-256 `a620f6a6ac6ed164d1bbf0eec56ca84d117233fcefa0303d8d732c0a648314c3`.
- Frozen v0.58 six original source selection SHA-256 `0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8`.

With pinned local original source/author dataset and local isolated Linux Docker available:

```powershell
python -m tools.audit_bibimbap_v062_topology12_native_DI --check
python -m unittest -q tests.test_bibimbap_v062_topology12_native_DI
```

The `--check` audit genuinely re-executes **all nine original source IFC edits and all three pinned Docker Python runs**, original author evaluator-only metrics and both adversarial actual Docker/rollback controls, and byte-compares the full deterministic JSON report with the frozen file. `--write` is exclusive-create, refusing historical overwrite. Any missing source, Docker image, local runtime or prior SHA mismatch fails closed, no fake offline execution claims.

After v0.62, **4/6 frozen prospective source tasks** have developer-controlled original-native D/I technical support: `topological_test_18`, `geometry_test_19`, `geometry_test_13`, `topological_test_12`. Four previous original task-specific engineering controls remain intact; **8/45 original editing tasks validated by developer fixtures, 37/45 not**. Remaining two fixed original tasks are **`topological_test_05` IFC4X3 Door+Opening creation** and **`geometry_test_03` IFC2X3 Door+Opening creation**. Original `geometry_test_19` repository evaluator still references a target GUID absent from exact original IFC; do NOT repair/guess scorer. All currently developed sources are **developer-exposed and not untouched independent holdouts**. Preserve the fixed six/source SHA and original population.

Public Hugging Face dataset card `cc-by-4.0` metadata does not establish every original IFC asset's chain of title/attribution or allow third-party model upload/retention. Pinned author repository checkout has no recognized LICENSE. There is no user-approved exact provider/model snapshot, source rights, USD budget, actual billed input/output token parity, match-feedback/context/ITT protocol or verified published-paper scorer revision. **Unconditional no-paid-model launch gate stays intact. Actual model trials 0, paid model calls 0, source IFC model-provider uploads 0.**
