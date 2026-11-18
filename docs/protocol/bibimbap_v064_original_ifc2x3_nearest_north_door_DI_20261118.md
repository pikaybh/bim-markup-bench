# v0.64 — Original IFC2X3 nearest-north Wall Door+Opening native D/I

**Research:** [Issue #243](https://github.com/pikaybh/bim-markup-bench/issues/243), stacked on v0.63 [Draft PR #242](https://github.com/pikaybh/bim-markup-bench/pull/242), exact parent d4038c3ea1cc73bc6228dae0bab430c89a34f8a2. Independent research repository pikaybh/bim-markup-bench, **not** Xim/BIXML production. Original author IFC, public question, scorer/GT, frozen reports, research main, earlier worktrees and stash are immutable.

## Original source IFC2X3 and public task

Public original BIBIMBAP question: add one Door to the Wall immediately **north (+Y)** of the Wall identified by its original public GlobalId. Source original IFC file 01/01/01_01_003.ifc, SHA-256 **88f315a0ec26c1e8bd5ea84fb254cf1d30b0ef143f03bbeffcee1dd8a69a2a59**. Actual native schema **IFC2X3**, not IFC4X3; project length **MILLIMETRE**, calculated SI scale 0.001; source-world shape meshes **METRES**. Source exactly **164 STEP entities, 52 IfcRoots, 3 IfcWall, 0 IfcDoor, 0 IfcOpeningElement, 0 IfcRelFillsElement, 0 IfcRelVoidsElement, 0 IfcSpace**. Three original independent SweptSolid Walls extend approximately X = −3.25 to 3.25m, Z = 0 to 6.096m, and occupy Y planes [−1.0,−0.8], [1.5,1.7], [5.0,5.2]m.

The public reference is the southern original Wall. Two walls are north of it, so the correct physical choice is the **nearest positive-Y wall** at approximately Y 1.6m, not the farther northern Wall at Y 5.1m. This selection is independently determinable from **public original question and actual source world geometry**, not a hidden author-answer injection into the host.

The pinned unmodified author repository evaluator data/tests/geometry_test_03.py uses its own nearest-positive-Y check and gives three Boolean metrics (object_exists, right_location, right_dimensions) and an integrity_constraint **FLOAT**, which is not forcibly converted to Boolean. The original author evaluator was imported **only in evaluator-only audit**, never in any model-facing D/I tool or native IFC compiler. Published-paper scorer-revision equivalence is **unverified**.

## Real IFC2X3 Door and hosted Opening geometry

For the correct developer-authored physical control, the genuine original IFC2X3 is edited with one new solid IfcOpeningElement at approximately X [−0.475,+0.475]m, Y [1.4,1.8]m, Z [0,2.2]m and one real represented IfcDoor panel inside at X [−0.45,+0.45]m, Y [1.575,1.620]m, Z [0,2.1]m. The new Opening voids the original middle Wall with IfcRelVoidsElement; the new Door fills it through IfcRelFillsElement; and the Door is explicitly contained in the **existing original building storey**, without changing any original containment attributes. Door native OverallWidth 900 and OverallHeight 2100 use native millimetres.

**Actual full-thickness CSG cut:** comparing the actual reopened SHA-pinned original Wall with the separate committed native IFC candidate Wall, the original Wall rendered solid volume decreases **0.418m³** (0.95m × 0.20m × 2.20m), with the original source 3D Wall bounding box unchanged and two non-host source Wall meshes and volumes preserved. This checks **real triangulated native solids**, not a fake relationship, moved Door name, typed editing plan, or invented XML bbox.

**IFC2X3 mandatory owner history:** unlike the earlier original IFC4X3 creation workflow, IFC2X3 requires OwnerHistory on newly introduced IfcRelRoots. Merely calling a generic API with no OwnerHistory caused exactly two additional native IFC2X3 schema findings. The trusted original-source-native compiler and independent actual Docker Python set **only missing new-root OwnerHistory references** to the already valid existing original host Wall OwnerHistory; no original STEP entity changes. Source and candidate schema findings are independently checked using the correct IFC2X3 ifcopenshell.validate source-error multiset. The actual validated solution introduces **zero new schema findings**.

**Source-baseline measurement correction:** an initial manual diagnostic accidentally called the supposedly source-before Wall-volume measurement *after editing the same mutable in-memory IFC*. This misleadingly produced a zero difference. The independent v0.64 source-native admission opens the **unmodified original IFC separately** from the output IFC, then measures actual before/after CSG geometry. The actual volume reduction was confirmed at 0.418m³; no false volume-based acceptance is allowed.

## Complete D-state, complete managed D-state, genuine OS-isolated Python I

**All three arms read exactly the same initial original source-anchored BuildingState XML, 2,185 UTF-8 bytes**, containing source IFC SHA, schema, native/world units, all existing original product/wall identities and absolute world-metre geometry, and a complete three-Wall original roster.

- **D_COMPLETE_XML_V064:** submit the **entire** original immutable BuildingState, all three original Wall GUID rows present, and explicitly exactly two **new final physical products** with unique IFC GUIDs, absolute world-metre Door/Opening bounding boxes and original Wall host and fill relationships. This is an absolute final state; no typed edit command, patch/diff, AST or hidden pre-filled answer.
- **D_MANAGED_FINAL_STATE_V064:** submit the **complete** three-original-Wall plus two-new-element managed final physical state, with the original IFC SHA and full original source BuildingState SHA. The trusted host **reattaches the immutable entire source** and validates against the full D source before creating the real IFC. Its initial compact source XML is 761 bytes. No partial missing-Wall row backfill.
- **I_NATIVE_DOCKER_V064:** independently authored general Python/IfcOpenShell performs native IFC2X3 file modifications with explicit commit() in the genuinely **pinned nonroot, no-network, read-only-root, capability-dropped, resource-bounded local Linux Docker**. It uses native IfcOpenShell APIs, not a fake AST-only worker, and independently fixes mandatory IFC2X3 OwnerHistory before commit.

All three paths share the **same** post-edit source-native IFC2X3 geometry/CSG/native Root/mandatory OwnerHistory/schema gate and total **25 tool-call limit**. **This is NOT a fair causal LLM comparison yet**: D vs I editing affordances, schema lengths, feedback, repeated read content, output-token burden, actual provider billed costs, generation settings and token budgets are not matched, and all current fixtures were authored by a developer.

## Independent native IFC2X3 acceptance and separate public-task correctness

**Structural native source gate** admits physically valid Door+Opening on any original Wall; the public nearest-north answer is **not a criterion or hardcoded GUID in the native validator**. Candidate must preserve all original 164 native STEP IDs/attributes, 52 original Root GUIDs and other original 3D geometry; create precisely one real IfcDoor, IfcOpeningElement, IfcRelVoidsElement, IfcRelFillsElement and storey-contained Door; have exactly these five new Root classes, no unrelated new Root or unreachable anonymous STEP entity; populate **all new IFC2X3 nonoptional OwnerHistory**; place Door within Opening with native mm dimensions agreeing with actual world-metre mesh; cut the host Wall fully across the **0.2m thickness** and match independent physically reopened original/edited Wall volume difference; introduce **zero IFC2X3 schema errors** beyond original baseline.

**Evaluator-only PUBLIC physical predicate**, completely separate from host, determines the Wall with minimum positive world-Y distance from the public referenced original Wall, checks Door ground-level Z and plausible width 0.6–1.5m/height 1.5–3m. A structurally valid Door with real Opening on the **farther** north Wall is admissible as native IFC but fails public correctness. A valid but undersized Door also fails public correctness. This separation prevents conflating valid IFC with a successful task response.

**Source-specific limitation:** strict unchanged-original STEP identity, exact 3-Wall schema, new-Root graph and conservative IFC representation requirements can reject alternate semantically valid IFC2X3 authoring styles. This may favor trusted D compilation over arbitrary Python I and is not universal semantic IFC equivalence.

## Real source-only developer controls

| Source-only control | Actual original native IFC D_FULL / D_MANAGED / pinned Linux Docker I | Independent public physical criterion | Unmodified author repository |
| --- | ---: | --- | --- |
| Normal 0.9m×2.1m Door on **nearest positive-Y Wall**, full-thickness hosted Opening | **3/3 PASS** | **PASS** | **1.00** |
| Same normal Door and full Opening on **farther north Wall** | **3/3 PASS** | **FAIL** (wrong Wall) | right_location=false; score below 1.00 |
| Too narrow and low 0.4m×1.2m Door with full Opening on nearest Wall | **3/3 PASS** | **FAIL** (dimensions) | **0.75** |

**Nine of nine** actual native original IFC2X3 files accepted. **Three of three** genuine isolated pinned Linux Docker Python scripts executed successfully. Independent source/edited whole 3D Wall mesh geometry, true CSG cut, native IFC2X3 schema, root preservation, new OwnerHistory and mandatory relations are checked. The canonical normalized *semantic* IFC digest agrees across D full/managed/general-I for equivalent cases; raw IFC SHA equality is **not** claimed because new GUIDs/STEP numbering/owner timestamps may differ. Original repository evaluator numeric and Boolean metrics agree across all D/I arms and remain evaluator-only.

Actually executed adversarial Docker edits: an Opening too shallow to penetrate full source Wall thickness was refused; Door without fills relation was refused; a valid native Docker commit followed by a second new Door insertion was refused **without changing last accepted IFC bytes**. A valid D XML commit followed by invalid incomplete original three-Wall roster preserved last accepted IFC and XML. Focused tests also check malformed IFC native mm, edited original Wall attributes, missing mandatory IFC2X3 OwnerHistory, fake Docker attestation, source SHA changes, duplicated original/new GUID, extra Root/orphan STEP objects, XML XXE/DTD, invalid/incomplete original Wall roster, and 25-call exhaustion.

## Frozen evidence, reproducibility, and non-claims

Six strictly additive research files: native IFC2X3 full/managed final-state compiler and independent physical CSG/schema oracle, three D/I sessions, evaluator-only original author/physical public/Docker audit, focused tests, frozen report and this protocol.

Frozen report: reports/bibimbap_v064_original_ifc2x3_north_door_native_DI_20261118.json — **SHA256 0499d218d2da2dcb5277c36ce33ae2fcb93ca40ef41fa0c9b079270e5ad7669d**. Frozen v0.63 parent report SHA256 77ea754501be7142319b425d31f17fd60b1ade9addb724ace4ecf7b70aba2437. Frozen original v0.58 six-source cohort SHA256 0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8.

Reproduce using the independently provisioned pinned original source and actual local Docker:

~~~powershell
python -m tools.audit_bibimbap_v064_ifc2x3_north_door_DI --check
python -m unittest -q tests.test_bibimbap_v064_original_ifc2x3_north_door_DI
~~~

The --check audit actually re-executes **all 9 original IFC2X3 D/I native edits, all 3 pinned Linux Docker Python instances and additional true Docker negative/rollback cases**, evaluator-only original author scores, independent public nearest-positive-Y physical criterion, then compares entire JSON bytes against the frozen report. --write uses exclusive creation; no overwritten frozen reports or fabricated offline substitute.

**All 6/6 originally selected original-source tasks now have technically validated developer D/I paths**, but **ZERO LLM-generated trials** have been conducted. Across the original **45 original public tasks**, **10 have developer-controlled technical support, 35 have not**. All six original sources have been manually inspected and are developer-exposed; they are **not unseen confirmatory holdouts**. Earlier geometry_test_19 original author scorer references a missing source GUID; it remains an independently disclosed defect without guessed official score. Original author repository lacks a recognized LICENSE and public dataset-card CC BY 4.0 does not by itself prove each IFC asset's source rights or consent to provider transfer/retention; exact paid model snapshot, model budget, billed D/I token fairness, feedback and official scorer-preregistration remain unapproved. **Actual LLM-generated trials 0; paid calls 0; original IFC uploads to model provider 0.** Preserve the unconditional model-provider no-launch gate.
