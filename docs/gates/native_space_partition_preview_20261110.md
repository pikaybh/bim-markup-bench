# G1 #15 — native IFC4X3 IfcSpace split + first-level boundary reconciliation, **sandbox proof only**

**2026-11-10.** Evidence: `reports/native_space_partition_preview_20261110.json`. Scope: single frozen, SHA-pinned BIM-Edit **public INPUT** `WAL-CRE-SPA-A-003` in the independent research repo. Original IFC SHA-256: `e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`. No hidden GT data or official scorer was read, no paid model calls were made and no source benchmark IFC was committed.

## Engineering outcome

Previously (#70), a manually authored declarative XML added one 4.45m × 0.175m × 2.8m Wall with two exact `IfcRelConnectsPathElements` T-junctions, independently matched by the imperative baseline. However, the original IfcSpace remained one 38.9375 m³ volume intersected by the new Wall. Space-boundary additions stayed blocked to avoid misrepresenting an unsplit room.

This PR implements **two deliberately distinct layers**:

1. `src/runtime/space_partition_preflight.py` — **pure read-only** native IFC geometry and first-level boundary surface planner. Requires exact eight-vertex/twelve-triangle axis-aligned cuboids for source IfcSpace and generated partition IfcWall, full source room width and height, strict interior location, input Space boundary surfaces with complete rectangular faces and outward normals, original 6-face coverage, and volume/face-area conservation. Each native first-level `IfcRelSpaceBoundary` is classified as `KEEP_NEAR`, `REHOME_FAR`, or `SPLIT_BOTH`. Unknown/missing/reversed surface, partial-height wall, invalid physical/virtual source relation or stale plan fails closed.
2. `src/runtime/space_partition_sandbox.py` — isolated **trusted, native IFC prototype** that only operates on an in-memory copy of a generated IFC and whose results are written into a disposable temporary directory. Recomputes the geometry plan *before* any mutation. It preserves the original near Space GUID, creates one new far IfcSpace with deterministic GUID, revises both independent rectangular swept solids, updates storey aggregation membership, rehomes/splits the original oriented boundary surfaces and adds two correctly oriented physical partition-wall faces. It never generates a virtual building element or changes another source Space.

The native result is then **written, reopened, and independently inspected from IFC**. This demonstrates the geometry + first-level boundary **feasibility for one source-supported room**; it is not an exposed edit API, and is deliberately **not** wired into the D0 declarative XML semantic-diff compiler.

## Quantitative reconciliation

| Surface action | Count |
|---|---:|
| Preexisting source-room boundaries | 7 |
| Keep on near (door-side) Space | 2 |
| Rehome to far Space | 1 |
| Split both (two slabs and two end walls) | 4 |
| New partition-wall face boundaries | 2 |
| Final combined boundaries near / far | **7 / 6** |
| New native IfcRelSpaceBoundary GlobalIds | **6** |
| All prior SpaceBoundary GlobalIds preserved | **Yes** |

| Body | Native volume (m³) |
|---|---:|
| Original single IfcSpace | **38.937500** |
| Near-space body | **29.066065** |
| Far-space body | **7.690935** |
| Intervening new Wall | **2.180500** |

The three new bodies sum to the original volume, with no overlap between the two resulting Spaces. Room geometry AABBs:
- Near: min `(0.175,2.90000,0)`, max `(4.625,5.23275,2.8)`.
- Far: min `(0.175,5.40775,0)`, max `(4.625,6.02500,2.8)`.

The near new partition face has outward normal `(0,+1,0)`, the far face `(0,-1,0)`. Original surface normals, the source's door/virtual boundary identities, source Space type/property relations, non-target Space geometry and its six boundaries all remain represented as before. All existing IFC Root GUIDs are retained.

The reloaded native split file can also be projected into the existing experimental XML: **3 Spaces, 10 XML-visible SpaceBoundary relations**, all native-edge binder checks pass, and an unchanged declarative XML recompile copies the split IFC **byte for byte**. The remaining IFC boundaries (slabs, door, virtual) stay opaque in this toy XML because its `SpaceBoundary` grammar only expresses Space↔Wall pairs.

## Important validation limitations

- `ifcopenshell.validate` reports **6 schema errors in the original public IFC**, and **4 in the temporary native split IFC**, with **no new error categories**. Remaining errors concern the source IFC's existing two `IfcRelSpaceBoundary` virtual references with absent mandatory `RelatedBuildingElement` (one in the target room and one in another Space). We preserve these instead of inventing an `IfcVirtualElement`. The source's two `IfcCurveBoundedPlane.InnerBoundaries` omissions in the target room are replaced with valid new bounded planes as part of the split; two other-room plane omissions persist. Do not claim full IFC schema validity.
- **New far IfcSpace is not assigned a separately justified IfcSpaceType or Psets**, so property/type semantics are incomplete even though original near-Space identity, typed relations and Psets are preserved.
- The native split is a *manually source-resolved sandbox reference*, **not a declarative XML edit handled by `compile_declarative_xml`**. This PR adds no user-facing mutation command and makes no claim that an LLM can produce the split. The independent imperative I0 Space-split oracle has also **not** been implemented, so **full D0/I0 parity for Space repartition is not proven**. The prior standalone Wall/T-join parity is unaffected.
- No wall Boolean body trim is claimed; the new Wall geometrically abuts the original walls and gets explicit native `IfcRelConnectsPathElements`, not an asserted physically trimmed junction.
- A complete IFC semantic policy for Space reidentification, room numbers, type assignment, QTO/Pset recalculation, source virtual boundary repair and secondary/adjacent-space boundaries is **not** justified here. Do not promote this proof directly to scored experimental use. The frozen 36 pilot remains unchanged; official benchmark success and LLM runs remain **zero**.

Standards background: buildingSMART IFC4.3.2 `IfcRelSpaceBoundary` — <https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelSpaceBoundary.htm>; `IfcRelSpaceBoundary1stLevel` — <https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelSpaceBoundary1stLevel.htm>. In particular, space-relative `IfcConnectionSurfaceGeometry` and geometric vs logical boundaries must not be conflated.

## Reproduce (local-only Windows 11, pinned Python/IfcOpenShell)

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_space_partition_preflight tests.test_space_partition_sandbox -v
.\.venv\Scripts\python.exe -m tools.verify_real_space_partition_preview
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The manual evidence script intentionally returns **exit code 2**, meaning **native sandbox geometry checks pass but task/evaluator/LLM gates remain blocked**. It generates the joined Wall candidate and new split model only under `TemporaryDirectory`, verifies original public IFC SHA unchanged, and serializes only sanitized numerical evidence and SHA-256 results into `reports/native_space_partition_preview_20261110.json`. Tests contain at least four fail-closed invalid input cases and saved/reopened native IFC checks.

## Next task (separate reviewed change)

Define a **fully declarative Space partition semantic diff** using two typed `<Space>` document states and explicit valid `<SpaceBoundary>` relationships rather than an imperative `<Split>` command. Bind it to the approved native geometry recipe while resolving Space GUID/type/Pset/virtual-boundary policy; independently implement the same in a Python/IfcOpenShell I0 oracle and prove exact native parity. Verify all inherited original IFC property/quantity semantics before making the functionality model-facing. Official scorer provenance, model budgets and source data rights still block a scored experiment.
