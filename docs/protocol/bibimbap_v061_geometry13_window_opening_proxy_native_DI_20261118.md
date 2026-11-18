# v0.61 — original Window + hosted Opening + three details world-X move, real declarative D versus isolated Docker I

**Issue:** [#237](https://github.com/pikaybh/bim-markup-bench/issues/237), stacked on [v0.60 Draft PR #236](https://github.com/pikaybh/bim-markup-bench/pull/236).
**Exact parent HEAD:** `e317a3965899274535d807e39ea8de64fe0fa3dd`.
**Scope:** independent research `pikaybh/bim-markup-bench` only, original author IFC, questions, evaluator and test inputs immutable. Research `main` and Xim/BIXML product are not modified. No paid model endpoints, provider uploads or original question/answer/GT transmitted to third parties.

## 1. Real original question and physical/native IFC source

The original *public* `geometry_test_13` asks to move **the window wider than 1.50m by +3m on the X axis**. Its actual pinned original native IFC4X3 source SHA256 is `a334c9f41e6d94307ecce9425647ce891b2b07321ab2b59020274ce683d46ee5`. This source has **two original `IfcWindow`**, **two hosted `IfcOpeningElement`**, **six `IfcBuildingElementProxy` details** (three per window: muntin, exterior trim, interior trim), and one Wall. Original source native dimensions/positions are in **millimetres**, but IfcOpenShell's `geom.create_shape` world mesh vertices are already **metres**. Native width is measured from actual world mesh: **1.60m and 0.60m**. Original type display names alone are not used for target selection.

A key source-native placement detail: the two Windows' own local placements both use the same shared source `IfcCartesianPoint` origin (zero). Their world positions are inherited from **distinct parent Opening placements**. Modifying this shared Window point directly would move unrelated IFC geometry. Instead, the actual source-native edit changes precisely **four unique independently owned placement points**: one selected Opening's placement X and three world-aligned detail Proxy placement X values, each by +3000 native IFC millimetres. The selected Window automatically follows its parent Opening. The resulting IFC actually reopens with **five original products** (Window, Opening, three details) shifted by **+3.000000 world metres**, the remaining native original products and relations unchanged and no new schema findings. A source-only geometry grouping uses actual 3D product world X centers and original filling/void links to identify the three proxies per Window, not hardcoded author-solution target GUIDs.

## 2. Three independent native editing arms

All three v0.61 model-facing sessions initially provide **exactly identical `BuildingState` XML (4,947 bytes)** containing immutable original native source SHA, IFC4X3/mm and world-metre framing, original product IDs/classes/names/geometry world bounding boxes, original Window-to-Opening-to-host links, and a full managed roster of **all ten original Window + Opening + detail elements**. No private author grading targets, hidden answers, or scorer code are in these model tools.

- **D_COMPLETE_XML_V061:** the model submits the **whole original BuildingState final state**, including unchanged original native product/geometry/relationship subtree and all ten original managed elements with explicit *absolute final* `finalWorldMinXM` (metres). No edit opcode, Python/AST, inferred missing rows, command or partial patch. All five members of exactly one original window assembly can change to a common bounded world X offset; the other assembly stays unchanged.
- **D_MANAGED_FINAL_STATE_V061:** the model submits a **complete explicit ten-element final-state roster** (1,437-byte initial compact XML) pinned to both original native IFC SHA and exact full original-state XML SHA. Trusted host reconstructs the entire immutable full source state, validates it as D_COMPLETE and applies only the source-bounded placement edit. Omitting rows is prohibited.
- **I_NATIVE_DOCKER_V061:** the model may submit arbitrary Python/IfcOpenShell source, genuinely executed in the original existing **pinned isolated Linux Docker** worker, non-root, no network, read-only container root, limited CPU/memory/processes, dropped Linux capabilities, bounded mounts and local pinned image SHA. The model must call `commit()`. Host accepts only a real original native IFC output passing the **identical independent** source-native scope/schema admission as both D variants, with no AST-only or fake executor substitution.

Each arm is bounded to **25 total tool calls**. An identical initial read does NOT provide the same editing affordances, output token lengths, multi-step feedback or provider billings. Real token parity/causal effect has NOT been measured, even though this research implementation is a technical prerequisite for such a study. The I source-read tool initially returns the same original XML; after an I edit, further source reads do **not** expose that edited native state as XML, while D read exposes its last accepted complete final XML. This is a known information/feedback asymmetry for future methodology review, not an unreported matched trial.

## 3. Source-only physical and independent native scope

The native scope and source schema oracle is **not aware of public question answer labels**. It accepts **either of the two original Window groups** moved by one consistent nonzero offset within a strict physical/native edit boundary (absolute offset ≤10m), preserving all ten managed original GUIDs/relations. For this particular original source, only **four exclusive original `IfcCartesianPoint` entities may change in native X**; no STEP entities are created/deleted; all original Root identities, other attribute/reference/shape/material/relationships and original source native unit metadata must remain unchanged. The oracle reopens candidate geometry and checks that exactly five source product world-mesh bounding boxes moved together by the same actual offset (X only), all other world meshes are unchanged, and independent **original source-versus-candidate IFC4X3 incremental schema-error delta adds zero new findings**. This catches incorrect mm/m conversions, moving the Window's shared placement origin, moving an Opening without related proxies, source identity/guid/order spoofing and changing unrelated Wall/geometry.

**Scope limitation:** This is a deliberately narrow original-source STEP-identity/point-placement engineering oracle. Another legitimate authoring method such as `geometry.edit_object_placement` may rewrite/re-number STEP placements or create different but geometrically equivalent IFC entity structure and consequently be rejected. This can systematically disadvantage general Python I compared with the trusted compiler and is **NOT proof of universal IFC semantic equivalence or fair D-vs-I causal benchmarking**. The checked geometries and exact accepted representation must be prospectively revisited before any full benchmark claim.

Source-only *public question physical correctness* is evaluated **separately**: the selected Window has actual original bbox width strictly >1.50m and the actual world displacement is precisely +3m. A short-window +3m edit and a wide-window +2m edit are both structurally valid source-native edits yet fail the public question predicate. The host checker does **not** silently call these invalid native candidates or leak correct answer GUIDs back to the tool.

## 4. Real test outcomes, original author repository metrics and limits

Three independently derived **developer-written** original-source control cases, each run as full-D, complete-managed-D and **genuinely isolated pinned Docker Python I**:

| Developer case (no target GUID leaked to report) | Actual source-native IFC D/M/I | Original repository evaluator score per arm |
| --- | --- | ---: |
| Wide 1.60m Window moved +3m, full Opening+3 Proxy group | 3/3 PASS | **1.00** |
| Narrow 0.60m Window moved +3m, full group | 3/3 PASS | **0.333333** |
| Wide Window moved +2m, full group | 3/3 PASS | **0.333333** |

Actual native IFC outputs **9/9** (three per arm) all reopen with **zero introduced IFC4X3 schema findings**, all 3 real Linux Docker Python executions attested, exact same **normalized native IFC semantic digest per source target/offset across D/M/I**, and immutable original source IFC SHA. Original author `data/tests/geometry_test_13.py` `execute_test` is imported **only in evaluator-only audit** and returned Boolean metrics matching across the three execution arms for each case, including source-based physical correct score 1.00. These metrics are from the pinned original **repository evaluator** and are **not independently proven equivalent to the scorer/revision used for a published paper's numbers**; **they are not LLM model scores**.

Adversarial *actual Docker* session that moved an Opening without the associated three proxies was rejected by the native oracle and did not commit a valid result. A genuine Docker valid first group move followed by another group move was rejected, with **the last-good native IFC SHA byte-for-byte preserved**. Full-D valid state followed by a missing-row XML was rejected and last-good XML and IFC preserved. Independent tests also reject changing shared Window point, moving unrelated Wall/product, changing a detail's Y, corrupting original source anchors, DTD/XXE, unknown/reordered/duplicate final GUIDs, incomplete roster, no-op, wrong native translation unit, fake Docker backend attestation and 25-call overrun.

**Important:** The earlier `geometry_test_19` original-author scorer remains **BLOCKED** because its evaluator references a Window GUID absent from its pinned input IFC. The new geometry13 successful author repository test does not resolve that defect. No original author source, GT or original data has been patched or guessed.

## 5. Frozen evidence and unfinished priorities

Six additive research-only artifacts: v0.61 source native geometry/full and compact final-state parser/compiler + independent native validator; actual Docker I + two D model-facing hosts; evaluator-only real Docker/author grader and rollback audit; 72 source-based security/semantic tests; immutable JSON report; this protocol.

**v0.61 report:** `reports/bibimbap_v061_window_opening_proxy_native_DI_20261118.json` SHA256 `a620f6a6ac6ed164d1bbf0eec56ca84d117233fcefa0303d8d732c0a648314c3`.

Frozen parent report SHA:
- v0.60 `e40204f381ccd17876708dd861c7031c1836cc41b7335e49909e797647f042ae`
- v0.58 original six-source holdout selection `0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8`

Reproduce in isolated Windows source-backed worktree:

```powershell
python -m tools.audit_bibimbap_v061_geometry13_native_DI --check
python -m unittest -q tests.test_bibimbap_v061_geometry13_native_DI
```

The audit `--check` genuinely re-executes all 9 IFC edits, all 3 real isolated Docker Python controls, original evaluator repository metrics (evaluator-only), real Docker malformed move rejection and post-good native rollback, compares the **entire deterministic report bytes**. `--write` creates exclusively and never overwrites previous evidence. Frozen report does **not** record original answer target GUIDs, code, original IFC raw data or author GT.

At present this is **3/6 of the six v0.58 selected source tasks native-D/I engineering verified**, and **7/45 original public task-specific developer-control verified**, NOT a completed or unbiased six-task LLM trial. Still missing **`geometry_test_03` IFC2X3 hosted Door creation; `topological_test_05` IFC4X3 exterior Door+Opening creation; `topological_test_12` source wall shortening 1m**. All six were preselected and remain exactly fixed; this case and two previously implemented source tasks have become developer-exposed, so the six are not wholly untouched independent confirmatory holdouts. Actual model trials **0**, paid calls **0**, provider IFC uploads **0**. Data-card CC BY 4.0 is not verified chain-of-title for each underlying IFC or permission for model provider transfer/retention; original author repo checkout lacks recognized LICENSE. Exact provider/model version, billable actual D/I input/output tokens, USD cap, valid scorer provenance, preprocessing/feedback parity, and user consent for source provider transfer remain unresolved. Existing no-launch firewall remains unconditional.
