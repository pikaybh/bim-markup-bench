# G1 #15 — Full declarative two-Space native IFC4X3 state diff + independent Python oracle (2026-11-10)

**Research status:** `PASS_ONE_TRUSTED_PAIRED_DECLARATIVE_SPACE_ORACLE_NOT_OFFICIAL_BIM_EDIT`. A precisely bounded, source-proven manual IFC4X3 execution pair succeeds. **Zero scored official tasks, zero model/API calls.** This is not evidence that an LLM can interpret the public natural-language instruction, and the full frozen 36-case benchmark is not executable/scored.

## Scope and prior dependency

The predeclared frozen public IFC input for `WAL-CRE-SPA-A-003` has SHA-256 `e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`. Before this change:

- A declarative XML source created a native IfcWall and its two `IfcRelConnectsPathElements` T-junctions, with independent imperative IFC parity.
- A source-verified native sandbox prototype split one existing room into two and reconciled oriented IFC first-level boundaries, but the D-arm's actual XML compiler **could not execute a Space change**, and no independent Python Space-split reference existed.

This change implements one **narrow whole-document Space-partition diff**, without modifying the research schema or introducing imperative XML commands.

## D0 — Declarative state-diff compiler, not a command bus

The agent-editable XML consists solely of ordinary `<Wall>`, `<Space>`, `<Connects>`, and `<SpaceBoundary>` document *state declarations*. The original Space keeps its stable ID and changes only `depth`. One newly named far Space has a fixed valid level, world box and deterministic GUID allocated by the trusted semantic binder. One new Wall and exactly two directed T-connections complete the partition. Existing and new wall/room boundary declarations must match actual native topology after compilation.

`src/runtime/space_partition_compiler.py` handles this specific graph-diff pattern:

1. Check exactly one modified original Space, one added Space, one added Wall, no removed product, no unrelated attributes or relation families; reject arbitrary IFC GlobalId claims and unsupported changes.
2. Construct a **separate temporary Wall/Connects-only XML snapshot** from source + the authored new Wall/Connections; invoke the existing validated compiler on the same frozen original IFC to produce a temporary joined IFC. This is an internal trusted compilation phase, *not* a model-callable operation.
3. Verify full native geometry/first-level oriented boundary plan from immutable original public input and joined IFC. Check both edited Space box declarations against the independently measured native partition. Missing, forged or mismatched geometry is rejected.
4. Allocate the far native Space identity from the **edited XML binder**, and apply the previously verified native Space repartition to the temporary IFC.
5. Atomically stage the complete IFC output; **reopen, reproject and bind the candidate IFC**. Compare every typed projected product (IFC identity, class, 9-decimal-projection-precision attributes) and every projected native relationship edge against the *entire* edited XML semantic state (not merely the changed Spaces). Check a concrete whitelist of allowed original native IfcRoot modifications, with no deleted original IfcRoot identities or unapproved new relationships. Only then publish the output file.
6. Revalidate the source IFC SHA-256 before and after commit; neither arm may alter it. All staging and intermediate models are temporary.

If any semantic mismatch occurs, the new output is **not created**. Tests explicitly cover forged far Space coordinates, unrelated source Space dimensions, fabricated native relation declarations, and omission of a required partition boundary.

This is **not** generalized arbitrary Space editing. The guard is source geometry bound and the existing native prototype's exact 7→13 first-level boundary pattern. XML is still a partial IFC-backed view, not lossless, native BIXML or a final public schema.

## I0 — Separately authored imperative Python/IfcOpenShell reference

`tests/oracles/python/independent_space_partition.py` is an independently written IFC authoring implementation. It **does not import the declarative XML compiler or native Space mutation function**. On the same SHA-pinned public IFC it:

- Independently creates the Wall using the preexisting imperative IfcOpenShell reference;
- Independently creates both T-junction relationships and consistent deterministic IDs;
- Reads native IfcSpace/Wall meshes and native first-level boundary surfaces in world coordinates;
- Writes a new far Space and rectangular swept-solid geometry;
- Rehomes/splits the previous oriented IFC boundary surfaces and makes the two partition faces;
- Saves an independently authored IFC to an isolated temporary result path.

The shared deterministic object-ID **contract** is intentional and predeclared; it does not make I0 author via XML or invoke D0 mutation routines.

The pre-existing **native-only independent IFC comparator** verifies both result IFCs match in `ifc_schema`, `identities`, `products`, `relations`, `property_sets` and `materials`. The dedicated test further checks all native `IfcRelSpaceBoundary` GUIDs, endpoint GUIDs, oriented surface minimum/maximum extents and normals, and resulting Space world bounds. Full-file SHA-256 need not match: STEP byte ordering differs between independently authored files.

## Source-only deterministic evidence

See `reports/manual_full_declarative_space_pair_20261110.json`; the evidence tool intentionally exits with code **2** as the official-model-run gating status. Important validated observations:

| Observation | Result |
|---|---|
| Shared frozen public source IFC | Yes, SHA-pinned |
| D0 compiler operations | CREATE_WALL; 2 × ADD_WALL_PATH_CONNECTION; SPLIT_SPACE |
| Independent I0 Space-split author | Yes, distinct code |
| Native-only six-category parity | **Pass** |
| Total IFC Spaces in each result | 3 |
| Native SpaceBoundary relations | 19 |
| New SpaceBoundary relationships | 6 |
| Far Space boundary count | 6 |
| Original IFC schema errors | 6 |
| D0 output IFC schema errors | 4 |
| New schema-error categories | **0** |
| New far Space independently typed and property-assigned | **No** |
| Official evaluator used | No |
| LLM inference or model-authored instruction attempted | No |
| Ground-truth IFC opened | No |

The source IFC has pre-existing invalid virtual SpaceBoundary fields. Preserve rather than invent missing virtual building elements. **Do not claim the output is fully schema-valid**, nor that the official BIM-Edit target required this particular Space subdivision. The far Space type, Psets, independent room identity/number policy, dynamic quantities and full information parity remain unproven. Original IfcRelSpaceBoundary identities are retained, and native trimmed wall Boolean geometry has not been established.

## Repeatable verification — Windows 11, offline

Run in the independent research repository with its pinned environment:

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_declarative_space_partition_compiler -v
.\.venv\Scripts\python.exe -m tools.verify_declarative_space_pair
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The trusted structured evidence script returns exit **2** despite a positive D0/I0 deterministic oracle, because the official evaluator, LLM task performance and fair two-arm prompt/inference controls are unverified.

All generated IFCs and task-specific temporary XML live only within temporary directories, not Git. Frozen task selection, benchmark data/GT separation, scoring formulas and evaluation budget stay unchanged. No downloads, model API calls, production services, or normative Xim/BIXML edits.

## Research maturity caveat

This closes the **deterministic compiler execution** and **independent Python parity** milestone for the second public frozen input. It **does not close full official task success, model comprehension, or fair D-vs-I experiment**. Future evaluations must independently establish the natural language instruction-to-state inference budget, target/source visibility controls, official/independent scorer provenance, and per-IFC data rights. The current results are developer-crafted deterministic oracles and cannot be reported as official 2/36 benchmark accuracy.
