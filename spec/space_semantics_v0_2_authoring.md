# Experimental v0.2 authoring state — explicit native IfcSpace type / Psets / QTO

**2026-11-10 | Issue #15 | New separately versioned candidate**. This is an independent BIM-markup-bench engineering feasibility test, NOT an approved change to the fixed toy v0.1 grammar, G2 LLM runner, 36-sample preregistration, scoring protocol, or Xim/BIXML product.

## Research motivation

Previously, the D0 XML `<Space>` state correctly compiled a rectangular partition and independent I0 Python/IfcOpenShell produced an equivalent IFC, but the newly created far `IfcSpace` had no independent `IfcSpaceType`, room-specific `IfcPropertySet` or `IfcElementQuantity`. Our source-semantic v0.2 **read-only** candidate established that the original input contains native type/Pset/Reference semantics omitted from v0.1 model-visible XML.

This PR tests whether a **separate, truly declarative final-state document** can explicitly author such metadata, and whether a separate imperative Python implementation produces the same native IFC structures.

**Important:** The public BIM-Edit instruction did **not** establish the new room name/number/type/Reference used in this proof. The demonstration's new room name `135`, type name `pilotroom 135:explicit partition` and Reference `pilotroom 135` are **synthetic manually chosen metadata**. They must NOT be misinterpreted as hidden benchmark ground truth or a correctly solved official task.

## Input and explicit state

Pinned original public IFC `WAL-CRE-SPA-A-003` SHA-256:

`e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`

The proof takes three trusted/source-backed documents:

1. Existing v0.1 declarative geometry-state XML (new Wall, two T-junctions, near/far Space bodies and boundary relationships), compiled unchanged by the existing `compile_declarative_xml`.
2. Existing versioned **read-only** v0.2 source semantic snapshot, rebuilt and checked byte-for-byte against the original public IFC. If any original Space type/Pset/value or source hash is forged, compilation aborts.
3. New, separate `SpaceSemanticsState` XML with the experimental namespace `urn:bim-markup-bench:space-semantics:authoring:v0.2`, fixed schema/version/source hashes and exactly **one** new Space node whose `localId` must match the new Space in the compiled v0.1 geometry. This final-state XML specifies an explicit Space `name`, `longName`, `predefinedType`, `compositionType`, separately named `Type`, two `PropertySet` declarations with typed `Property` values, and `Quantities` with authored `netFloorAreaM2` and `netVolumeM3`.

This **is not a command-language API**: no `<Create>`, `<SetProperty>`, `<SplitSpace>` or arbitrary execution tag is supported. The trusted writer infers that a new native Space already exists from the verified v0.1 document-state diff, then binds the independent metadata state onto that single native identity.

The old `toy_markup_v0.xsd`, `src/runtime/ifc_projection.py`, `src/runtime/compiler.py`, the G2 agent-input runners, benchmark manifest, experiment runner, and evaluation metrics remain entirely unchanged.

## Conservative native semantics policy

Only one concrete, source-backed family is supported in this **offline prototype**. Native output creates:

- New `IfcSpaceType` (distinct deterministic GlobalId; explicit name; PredefinedType `NOTDEFINED`) and one `IfcRelDefinesByType` to the *new* far `IfcSpace`.
- New `Pset_SpaceCommon` with explicitly authored `Reference` (IfcIdentifier) and `IsExternal=false` (IfcBoolean).
- New `Pset_SpaceHeaterTypeCommon` with separately authored identical `Reference` (IfcIdentifier). Two distinct native `IfcRelDefinesByProperties` relationships.
- New `Qto_SpaceBaseQuantities` with `IfcQuantityArea.NetFloorArea` and `IfcQuantityVolume.NetVolume`, plus a native `IfcRelDefinesByProperties` link.

All eight new metadata `IfcRoot` identities (type, type rel, 2 Psets, 2 Pset rels, QTO, QTO rel) have a deterministic, cross-arm documented GlobalId contract: UUIDv5 over source SHA, far Space GUID and metadata role. **The new far Space GUID is already allocated by the v0.1 binder** and not recycled from an existing room. Native `Name` and `LongName` are taken exclusively from the authored XML.

The trusted writer independently recomputes geometric room area and volume from the **exact rectangular native IFC mesh**, not the LLM-supplied quantity fields. The specified values **must match the native box within 1e-7**, otherwise the entire output is rejected before commit. This does **not** prove general net-area calculations involving columns, irregular boundaries or deductions: it is restricted to this one rectangular source/geometry case. Source original IfcSpaces have no QTO, and no QTO is fabricated for them.

The writer rejects duplicate existing room names, identical source type names, reused source `Reference` identifiers, mismatched Psets, wrong `IsExternal`, mismatched Space local IDs, stale input/source observation digests, non-finite/incorrect quantities and unsupported XML commands. Previous native `IfcRoot` products, properties, Psets, type relationships and geometry must remain unchanged except the **already-new far Space**, which now receives its declared name/type/quantities.

After staging the whole IFC, the writer reopens and validates new typed relationships, all expected Pset value types/values, native QTO entity families and geometric quantities, preserved source Space metadata, exact whitelist of newly introduced metadata root GUIDs, preservation of all other original `IfcRoot` entity serialisations, and unchanged room native geometry. Only then is the output atomically made visible. The source IFC is hashed before and after and never overwritten.

## Independently authored imperative I0 reference

`tests/oracles/python/independent_space_metadata_v02.py` writes the same metadata directly via IFC authoring calls, **without importing the D0 XML parser, metadata writer or compiler**. Its inputs are separately authored Python values, not a D0 result IFC or hidden benchmark GT. It uses its own mesh-derived QTO and the preregistered GUID contract.

The complete I0 pipeline first independently writes the Wall and path-connections, then independently partitions native IfcSpace and oriented first-level SpaceBoundary surfaces (earlier verified tests), then writes the new type, Psets and QTO.

The existing independent IFC comparator proves six-category parity (schema, identities, products, typed geometric relationships, Psets and materials). A separate native **Space metadata/QTO relation signature** checks every existing Space plus the newly typed Space: native `IfcRelDefinesByType` and `IfcRelDefinesByProperties` GlobalIds and endpoints, `IfcSpaceType` names, exact typed values and `IfcElementQuantity` area/volume values. Neither arm is allowed to borrow existing room Reference/room-number semantics.

## Observed manual engineering results

| Evidence item | Observation |
|---|---|
| Source IFC original SHA remains unchanged | Yes |
| V0.1 native geometric Space split compiler changed | No |
| D0 XML authoring produced native new room metadata | Yes |
| I0 separately authored IFC matches D0 | **Yes** |
| Native typed source and new-room relation/QTO parity | **Yes** |
| New native `IfcRoot` metadata objects | 8 |
| New room type relations / property+QTO relations | 1 / 3 |
| Explicit new room rectangular NetFloorArea / NetVolume | **2.7467625 m² / 7.690935 m³** |
| Original IFC schema errors | 6 |
| D0 / I0 output IFC schema errors | 4 / 4 |
| New schema-error categories introduced | **0** |
| Native IFCs fully schema-clean | **No** — inherited source errors persist |
| Hidden benchmark GT / official evaluator loaded | **No** |
| Official scored tasks / LLM calls | **0 / 0** |

The two native IFC binaries may have different full-file SHA-256 values due to STEP ordering. The native object identities, geometry, source metadata, typed relations, Psets and values are independently verified equal. Structured evidence is saved as hashes/counts/status only in:

`reports/manual_explicit_space_semantics_v02_pair_20261110.json`

The evidence tool intentionally exits **2**: engineering D0/I0 parity **passes** but model-authored performance, fair context budgets, native semantic completeness and official scoring remain **blocked**.

## Reproduce on Windows 11 (offline, pinned IfcOpenShell)

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_space_semantics_v02_authoring tests.test_space_semantics_v02_independent_pair -v
.\.venv\Scripts\python.exe -m tools.verify_space_semantics_v02_authoring_pair
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

No original IFC is checked into Git; all candidate output IFCs are created in disposable temporary folders and discarded.

## Remaining scientific barriers

1. This explicitly selected new room identity and properties are **manual synthetic experimental data**, not inferred from the natural-language benchmark request; no official task correctness is established.
2. The v0.2 editing schema is **not authorized in the model-facing D0 runner**; adding this overlay would increase context/authoring complexity. Equal visible source bytes alone do not establish fair effective tool/inference budgets or equivalent task information.
3. The native property set family/enum/quantity format is a deliberately limited subset; no generic roundtrip for arbitrary IFC type/quantity/property sets or room-number semantics is claimed. Rectangular `NetFloorArea`/volume is a geometric example, not a full spatial quantity semantics specification.
4. The source IFC's preexisting virtual-boundary schema violations survive (4 diagnostics remain in each output). Therefore neither result can be called fully schema-conformant.
5. The official scoring artifact/provenance, full licensed inputs and actual controlled LLM trial are still separate incomplete research gates. A future promotion to an approved experimental arm or pre-registered ablation requires explicit review/versioning. Do not silently modify toy v0.1 or misreport a developer-authored oracle as accuracy on the frozen 36 tasks.
