# v0.44 — Original four UPDATE/DELETE IFC4X3:mm native STEP/semantic source facts as strictly READ-ONLY model-facing XML

Issue [#203](https://github.com/pikaybh/bim-markup-bench/issues/203) · stacked from v0.43 [Draft PR #202](https://github.com/pikaybh/bim-markup-bench/pull/202) exact parent HEAD `711bc5804406dbd99d4f358f8fa5882c15691197`.

## Motivation and original cohort integrity

The v0.43 frozen original-45 parity audit discovered four **real original public UPDATE/DELETE source inputs** that the XML backend's *actual* model-facing `read_building_xml` tool could not read. The failure is original geometry projection support, not a task/LLM failure:

| Original public task | Actual original IFC form | v0.43 default & research | v0.44 separate explicit source-read flag |
| --- | --- | --- | --- |
| `geometry_test_14` | One original native `IfcSlab` with `SweptSolid` source | unsupported | readable immutable original STEP/XML |
| `geometry_test_15` | Four native `IfcColumn` products with `MappedRepresentation` | unsupported | readable immutable original STEP/XML |
| `topological_test_11` | Two Columns, two Slabs, seven original clipped Walls, two actual Spaces | unsupported | readable immutable original STEP/XML |
| `topological_test_17` | Ten native Columns and two Slabs, with original storeys | unsupported | readable immutable original STEP/XML |

Each input is **the original published IFC4X3 file in millimetres**, not an invented IFC, simplified replacement model, created task answer or normalised/metre-reserialized source. The four original source SHA256s and associated original public question SHA256s are pinned in both the original code and the independent oracle. SHA pins verify before reading, afterwards, and during frozen audit.

- Original author Git HEAD: `667004e16bd38fd7d538bcee56191465429fd975`
- Original data Git HEAD: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`
- Original 45-question CSV SHA256: `21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b`
- Previously frozen v0.43 report SHA256: `eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf`
- Original population: 45 published tasks, 15 CREATE/15 UPDATE/15 DELETE, 31 unique source IFC byte hashes; **unchanged**. No original benchmark task, question, source IFC, grader, hidden GT, task-specific solution or prior frozen report modified.

## Exact new model-facing read capability (NOT update/delete support)

New isolated, explicit opt-in:

```python
XmlSourceEditSession(
    public_original_native_mm_ifc,
    isolated_trial_folder,
    experimental_original_native_readonly_v044=True,
)
```

The opt-in accepts **only four exact source byte hashes**. It is mutually exclusive with prior v0.38/v0.39/v0.40/v0.41/v0.42 research gates; the default public paid runner still does **not** enable any research variant. A dedicated `spec/original_native_step_readonly_v044.xsd` is used; the original default authoring XSD is unchanged.

The familiar **two model-facing tools** remain `read_building_xml` and `submit_building_xml`, but descriptions explicitly warn the model that the complete source is **immutable and UPDATE/DELETE is unsupported**. The former returns a single complete XML `Building` containing a `OriginalNativeIFCSource` with seven source sections:

1. **Products** — original `IfcProduct` GUID, class, original Name, Description, Type and PredefinedType where present, original STEP entity ID and placement/representation STEP references, `NONE_READ_ONLY`.
2. **Relations** — every real original native `IfcRelationship` GlobalId, class, source STEP ID and **every direct original relationship endpoint** with original role, STEP reference and native source GUID when present. No fabricated room contacts or synthetic native relationship.
3. **PropertySets** — native original `IfcPropertySet` GUID/name/step ID and every contained property original name and typed nominal value when one exists, source-derived only.
4. **Materials** — every actual original `IfcMaterial` step ID, name and source metadata (materials linked through exact original relations and full original STEP records).
5. **LocalPlacements** — every original `IfcLocalPlacement` ID, relative/parent source references and full 4×4 source placement matrix (in the original native-mm coordinate frame, not silently relabeled in metres).
6. **WorldGeometry** — physically opened native IFC source geometry on every represented original `IfcProduct`, original GUID/class, representation STEP ID, actual original-source world mesh ordered 1 μm metre-coordinate vertices and triangle indices, source bounds and exact stable geometry hash. A genuine IFC representation with unavailable world mesh must say `SOURCE_NATIVE_GEOMETRY_UNAVAILABLE`, **never** fake a shape. In the four pinned sources all 30 represented products had valid independently verified native meshes.
7. **NativeStepRecords** — **every literal original IFC DATA entity line**, original `#stepId` and exact original source IFC class and text, in the same **order and exact line text as the original source mm IFC**, *not* a regenerated IFC; no missing/new/duplicate records. This completes the native original IFC DATA entity coverage within the XML view. It does **not** claim the IFC HEADER is included or that IfcOpenShell convenience API methods are callable by the XML model.

The read-only session skips metre-unit IFC normalization entirely: `self.normalized is None`, and no temporary IFC copy, native candidate, or attempt-directory IFC is created. This ensures a source-only research mode does not even generate a converted native source file. All pre-existing native authoring modes retain their original normalization/writer path.

**The source STEP portion is a read-only quotation of original native IFC data inside XML**, not executable commands or a changed XML task grammar. Exposing source facts is not a model answer or a native mutator.

## Measured improvement and absolute boundary

| Original case | Actual native IFC DATA lines | Actual native relationship GUIDs + direct refs | Source products | Property sets | Materials | Placements | Physical world meshes | Model-visible XML bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `geometry_test_14` | 119 | 21 | 5 | 15 | 1 | 5 | 1 | 39,513 |
| `geometry_test_15` | 166 | 29 | 8 | 24 | 1 | 8 | 4 | 60,509 |
| `topological_test_11` | 579 | 73 | 17 | 51 | 3 | 17 | 13 | 172,263 |
| `topological_test_17` | 440 | 69 | 17 | 60 | 2 | 17 | 12 | 151,525 |
| **Total** | **1,304** | **192** | **47** | **150** | **7** | **47** | **30** | **423,810** |

Total **252 native source world-mesh ordered vertices and 384 native source world-mesh indexed triangles**, verified at native source original-mm → renderer world metre coordinate precision 1 μm. The original IFC full STEP DATA exact source text (not a new geometry) is the source of truth. All four XML reads remain bounded by the existing 300,000-byte model-source limit **per original file**.

**v0.43 best-available research reads were 41/45; with four additional explicitly gated source readers the collection of separate research modes can now READ 45/45 original task inputs.** This is **not** `45/45` native task support. The unmodified default experimental runner remains **36/45** XML reads (9 original backend read failures). The new v0.44 source representation **does not integrate with old XML native writers**. The four new modes give complete original DATA source text and structured references but *no permitted mutation*.

The actual `submit_building_xml` tool was invoked twice per original source with the unchanged XML and a manipulated XML, for **8 negative submissions**. Every one returned `UnsupportedArm` `V044_READ_ONLY_ORIGINAL_NATIVE_SOURCE_UPDATE_DELETE_MUTATION_UNSUPPORTED`; the original XML remained last-valid, **no native IFC candidate or attempt directory was created**, the original public IFC SHA did not change. This is not a successful UPDATE/DELETE or baseline original author score.

## Independent test and falsifiability

The host source projector `src/runtime/experimental_v44_original_native_step_readonly.py` and independent `tools/bibimbap_v044_independent_original_native_source_oracle.py` are separate implementations. The oracle **does not import the v0.44 projector, session, compiler or author scorer**; it rereads the true original source IFC bytes and independently verifies original IFC4X3/mm, every STEP DATA line text/STEP ID/order/class, exact Product/Relation GUID and original relationship endpoint, every PropertySet/property and Material value, actual native placement matrix and independently tessellated native world vertex/triangle/bounds/hash. Original native source is hashed before/after read.

The dedicated v0.44 XSD enforces the fixed seven-section layout and key identity fields; the independent oracle additionally fails closed on source text/identity/metadata/geometry deviation. **86 positive and negative focused tests** cover original 45/31 population/CSV input hashes, every actual source read, original mm geometry, all exact native STEP entities, source metadata, full source spoof/omission/reordering, fake GUID/IFC class, relation endpoints, PropertySet names and values, Material names, placement frame/parent step IDs, world mesh points/triangles/digests/bboxes, XML DTD/XXE and foreign inputs, mutually exclusive original source flags, all eight real fail-closed submission attempts, last-valid state, previous frozen report/source preservation and byte-identical rerun.

FROZEN machine result (cannot be overwritten via auditor, `open("xb")`):

`reports/bibimbap_v044_original4_native_STEP_readonly_20261117.json`

SHA256: **`dc58535db3dbec85ba610d3e8b9104c660c4bf0e3e019f9a20ee3a32a012281a`**.

### Reproducible offline commands

From isolated Windows project Worktree:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m tools.audit_bibimbap_v044_original4_native_step_read `
    --author (Join-Path $base 'bibimbap-author-upstream') `
    --data (Join-Path $base 'bibimbap-author-data') --progress

& $py -m unittest -q tests.test_bibimbap_v044_original4_native_step_readonly
```

This task invokes **zero paid provider calls, Docker executions, original author grading operations or actual matched XML-vs-Python LLM trials**. It never modifies the original task IFCS, default XML XSD, original grader/GT or Xim/BIXML product repository. It does not merge into research `main`.

## What this research result does not justify

- **Same source data access is not same interface**: the XML model gets source IFC data lines and structured summary inside a 39–172 KB XML text, whereas the Python model could run arbitrary IfcOpenShell operations, dynamic relationships/geometry queries and edits. Token budget, latency and API ergonomics are not equal. The original `IfcOpenShell` methods are not magically represented by static XML source records.
- **No original task-specific answer hint**: the compiler/projector emits source facts and original geometry, not the correct edit amount, deletion set or any original benchmark evaluator truth. No task-specific D0/I0 pair or author score has been created here.
- **Read-only cannot be compared to full native writes**: the four original UPDATE/DELETE IFCs now have model-visible source text, but *their XML arm explicitly cannot commit native IFC modifications*. They are still not eligible for an unconstrained matched native scoring experiment. The prior original CREATE task-specific developer D0/I0 controls remain **5/15**, and the other original source readers still have v0.43 metadata gaps.
- **Prior 45/45 information/write parity is not proven**: this applies to exactly the four source SHA-pinned original inputs. Old 27 readable unique original sources still require a principled metadata/relationship comparison/enrichment; other 41 task source-read variants are separately implemented and do not share one single uniform XML native writer. No original 45 full source/authority parity is claimed.

**Next priority v0.45:** preregister and implement true native-IFC original UPDATE/DELETE editing from complete declarative XML for these four original sources with strict physical/original-identity/original-author semantics, otherwise explicitly preserve unsupported cases, while assessing source metadata + native edit parity on the remaining source subset. Only once same-information, same-native-authority and benchmark post-freeze constraints are empirically satisfied should actual matched LLM D/I trials be authorized.
