# G1 #16 — Public-instruction-derived spatial Wall, D0/I0 source-only native IFC

**2026-11-10 · Status: PASS_PROMPT_GROUNDED_WALL_TWO_JOINS_SOURCE_ONLY_FULL_ORACLE_BLOCKED.**

This is one trusted **non-LLM, non-scored** deterministic source-only experiment for the frozen public task `WAL-CRE-SPA-A-003`. It advances the previous geometry-only and manually selected path-join experiments by deriving both host-Wall identifiers, the room identifier, right-of-door +Y offset, thickness and height from the **original public instruction** and verifying all against the actual original IFC.

It does **not** establish full BIM-Edit benchmark success, a new Space definition, complete model-facing fairness, or any model language advantage.

## Pinned source and exact scope

- Task: `WAL-CRE-SPA-A-003`, one of the unchanged 36 original candidates.
- Original task JSONL SHA-256: `9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83`.
- Frozen 36-candidate manifest SHA-256: `75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694`.
- Pinned original public IFC SHA-256: `e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`.
- Exact public instruction SHA-256: `31a00588498f68ef6791a133b033cc3da442749d5a237e76f0f5817cf095d14d`.

The public instruction specifically requests a wall orthogonally between two identified walls, beginning **1.3025 m in world +Y from the right-hand side of the door when viewed from inside the identified room**, thickness **0.175 m** and height **2.800 m**. The task does **not** specify a new room's Name/Type/Reference/Psets/QTO or explicitly require a particular new `IfcSpace` partition.

The trusted parser recognizes **only that exact public instruction grammar and those frozen numeric constraints**. It rejects extra or changed commands, non-frozen distances, mistaken direction/viewpoint, duplicate/wrong-type IFC IDs and unknown references. The original input is checked against the separately published remote file hash before any work. The task payload sent into either source-only context contains **only** `{task_id,instruction,input_file}`; grader-only `target`, `ground_truth_ifc` and `evaluation` are not inspected or passed into those contexts.

## Actual native construction

**D0 (declarative):** Open the real existing G2 `building.xml` source-only model context; append exactly one `Wall` declarative object with `id/level/x1/y1/z1/x2/y2/z2/height/thickness` and exactly two `Connects` declarative final-state relationships. The `SourceOnlySession` accepts this as an XML whole-file rewrite. A **separate trusted runtime outside the authoring loop** uses `TrustedCompilationController.compile_accepted` to produce IFC. **No procedural `<Create>`, `<Move>`, `<Update>` or `<Split>` commands are authored.**

**I0 (imperative):** An independently authored IfcOpenShell-only source reference from `tests/oracles/python/independent_ifc_oracle.py` creates the new native wall with the same public-source-derived coordinates, then independently creates two `IfcRelConnectsPathElements` relations using deterministic identity seeds. It does **not** call the D0 XML compiler or use the XML model to author the result. All candidate output IFCs remain temporary.

The native source-only geometry interpreter also checks actual room/wall/door IFC relationships and a single hosted door; it uses the door's observed right-hand jamb and the source room geometry, not a hidden official reference.

## Verified results

| Source-only native assertion | Observation |
| --- | --- |
| New Wall world bounding min (m) | **(0.175, 5.23275, 0.0)** |
| New Wall world bounding max (m) | **(4.625, 5.40775, 2.8)** |
| Prompt-specific new T-path joins | **2** (`ATPATH/ATSTART`, `ATPATH/ATEND`) |
| New Wall class, geometry and native relation endpoints | D0/I0 agree |
| Independent IFC comparison categories | **6-category IFC schema, identity, products, relations, Psets, materials** — parity |
| Original `IfcRoot` GUIDs and native relations | Preserved |
| Original `IfcRelSpaceBoundary` inventory | Preserved (no invented split) |
| Original room overlap with new Wall volume | **2.1805 m³** |
| Separate D0 and I0 IFC file SHA-256 values | Recorded in sanitized report |
| D0/I0 IFC byte-identical | **No** — not required by semantic parity |
| Full native IFC byte repeatability across runs | **Not proven** (some IfcOpenShell-created relation IDs may vary) |
| Official target-space semantics/complete task oracle | **Unverified** |
| Actual LLM calls / official tasks scored | **0 / 0** |

The new wall overlaps the preexisting `IfcSpace`. An independent experimental v0.1 source-state splitter and v0.2 typed Space authoring prototype already exist, but **this prompt does not justify a unique new Space name, type, reference or Psets**. An arbitrary manually chosen name `135` cannot be taken as official task correctness. Therefore this proof **does not** silently split the original room or add made-up spatial metadata, and it remains **BLOCKED** for full official task completion.

The two native outputs agree across independent IFC semantic observations but **do not have to share a raw file hash**. Existing IfcOpenShell operations may generate unrelated, implementation-specific relationship identifier bytes. The emitted hashes describe each exact run; they are not advertised as repeatable across runs. Regression tests compare stable semantic evidence rather than fabricating exact raw-byte reproducibility.

## Model input fairness and security boundaries

The real existing model-visible source observers for D0 and I0 provide the **same byte-for-byte** task ID, public instruction, v0.1 source XML, XML language specification and original input IFC digest. Their component SHA-256/byte counts are recorded, without storing the prompt or identifiers themselves. The I0 view additionally contains **1,113 bytes of API reference notes**; the generated Python executable is currently not available under a verified Docker Linux OS sandbox. Tool feedback, tokenized provider context and paid token budgets are **not** matched or approved by this demonstration.

The manually produced declarative XML edit and Python mutation recipe exist **only in this trusted developer test**, never as an example or instruction to either future authoring model. The original IFC is not modified. No benchmark GT file was opened, no official IFC scorer executed, no model inference called and no provider charge incurred.

## Reproduce

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_prompt_grounded_spatial_wall -v
.\.venv\Scripts\python.exe -m tools.verify_prompt_grounded_spatial_wall
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The standalone proof tool exits **2 intentionally** despite valid source-only pair parity: it must not be mistaken for approved official/paid G1/G2/G3 execution.

Files:
- `tools/verify_prompt_grounded_spatial_wall.py`
- `tests/test_prompt_grounded_spatial_wall.py`
- `reports/g1_prompt_grounded_spatial_wall_20261110.json`

The tests include strict public input parsing, real IFC geometry and T-connectivity, source immutability, D0/I0 matched common information, repeated *semantic* evidence checks, forged hidden `target/ground_truth_ifc/evaluation` metadata, invalid/missing/wrong-type GUIDs, wrong orientation/dimensions, native topology mutation rejection and report leakage checks.

## Next blockers

- Uniquely justify any new Space split and metadata from **public** instruction and source evidence, or restrict the benchmark oracle explicitly to wall geometry and native joins only; do not use private GT to instruct an authoring model.
- Verify a full instruction-dependent native IFC triple through an independent evaluator and document exactly what the official BIM-Edit rubric expects. Official evaluator code and scorer equivalence remain unverified.
- Complete full frozen 36-task coverage without post-hoc task reselection, correct both arms' tool/token feedback and enable genuinely isolated generated Python only after a fresh Docker kernel proof and authorized budget.
- **No official model benchmark result or claim that XML outperforms Python.**
