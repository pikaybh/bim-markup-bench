# G1 #15 — native IFC4X3 T-path junctions on frozen public Wall create input

Date: **2026-11-10**. Scope: **one narrow, source-verified native Wall-to-Wall topology operation** in the independent research repository, not BIXML/Xim. Status: **BLOCKED_NATIVE_SPACE_BOUNDARY_AND_OFFICIAL_EVALUATOR** for the full task.

## Source-only task and standards evidence

The unchanged 36-task preregistration candidate contains `WAL-CRE-SPA-A-003`. Shared pinned public input IFC SHA-256:
`e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`.

The real task creates an interior Wall between two existing parallel Walls. Their actual 3D body surfaces meet the newly created Wall at its **start** and **end**, respectively, while touching the original wall **along its path**, not at the original wall endpoint. This is a geometric **T-connection**. The original IFC already contains four `IfcRelConnectsPathElements` relationships with explicit `ATSTART`/`ATEND` types; this is established from public *input only*, not an answer oracle.

Standards:
- buildingSMART IFC4.3.2.0 `IfcConnectionTypeEnum` documents T-shapes as an **ATPATH** side and an **ATSTART** endpoint: https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcConnectionTypeEnum.htm
- `IfcRelConnectsPathElements` is a subtype of `IfcRelConnectsElements`, supporting zero-length priority lists and explicitly oriented endpoint/path enum fields: https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelConnectsPathElements.htm

## Implementation and native proof

The markup-editing interface remains **declarative**: a new `<Wall .../>` node and two `<Connects from="existing_host" to="new_wall" />` relationship nodes. There are **no** XML mutation commands or API calls available to the LLM.

The trusted backend:
1. Finds a **source-existing** host wall and a **deterministically new** Wall, both belonging to one existing storey.
2. Validates actual IFC native world mesh extent against the host's typed Wall centerline, thickness, height and vertical axis. Confirms the new segment is at 90° to the host axis and exactly meets an *outer host side face*, with its entire thickness inside the host's path.
3. Rejects wall connections that cross/overlap existing host door/window openings. Rejects reversed relationship declarations, missing contact and unsupported geometry; these cause no result IFC file to be published.
4. Creates exactly two `IfcRelConnectsPathElements` for this real input, one with `RelatingConnectionType=ATPATH, RelatedConnectionType=ATSTART` and one with `ATPATH, ATEND`. It does not silently upcast to generic `IfcRelConnectsElements`.
5. Reopens the output IFC, verifies relationship **concrete subtype**, correct source and new-Wall GUIDs, connection enums, empty priority lists, absent fabricated connection geometry, native new-Wall 3D bounding box and preservation of every prior native IFC relationship other than the necessary building-storey containment member addition.

The independent **I0 Python/IfcOpenShell** reference uses the *same public source IFC*, independently builds the wall and path relations, and implements the shared deterministic identity contract on its own. Both IFCs pass the existing independent native-only comparison: `independent_D0_I0_ifc_parity=true`. The two full-file byte hashes can differ due to independent STEP ordering. This test intentionally resolves the geometry/targets **inside a trusted manual source-only oracle**, not from any model output.

Reproduction:
```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_native_t_path_junction tests.test_topology_edits -v
.\.venv\Scripts\python.exe -m tools.verify_real_t_path_pair
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```
The middle command intentionally returns **exit code 2**: geometry/connection execution passes, but scientific full-task/scoring gates remain blocked. It stores no candidate IFC, passes no grader GT to either arm, makes no network/model API calls and reports only sanitized statistics and SHA-256 hashes. Structured evidence: `reports/manual_real_t_path_20261110.json`.

## Space-boundary gate — do not invent the next relationship

The public original **IfcSpace** remains a single volume (axis-aligned world cuboid). The new partition's native 3D bounding box overlaps this unsplit Space by **2.1805 cubic metres**. The source Space currently has pre-existing `IfcRelSpaceBoundary` relations, including geometry-backed surfaces and a virtual boundary.

A naive extra `<SpaceBoundary space="old_room" element="new_partition" />` would claim a valid first-level boundary while the old Space geometry still occupies the partition's thickness, potentially misrepresenting the room's topology and area. **Explicit native space subdivision/reconciliation with correct oriented surfaces** must be specified and verified before such a new boundary may be exported. buildingSMART defines space boundaries **from the Space** and differentiates level-1/level-2 boundaries: https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRelSpaceBoundary.htm

The added negative test proves that attempting to add `SpaceBoundary` before this gate is resolved fails closed with no result IFC. Evidence:
- `new_native_path_joins=2`
- `native_room_wall_volume_overlap_m3=2.1805`
- `new_wall_native_space_boundaries=0`
- `space_subdivision_or_reconciliation_verified=false`
- `space_subdivision_required_by_official_target=null` (**unknown**, not inferred from hidden GT)
- `native_join_body_boolean_geometry_verified=false`: semantic/parametric path relationship is verified, but no physical Boolean trim of both walls is claimed.

## Research status and remaining work

This is a **second real-input deterministic geometry/topology pairing**, NOT a scored BIM-Edit task or LLM result. The sample is unchanged and only one frozen task's *manual* oracle has progressed here. Model instruction comprehension, fair-arm input context, official scorer availability/numerical parity, all other task coverage and per-IFC licensing remain unresolved.

The immediate next engineering priority is a **separate, independently specified IfcSpace split/geometry & space-boundary reconciliation vertical slice**, without editing the published sample or using target/GT IFC to design the solution. This requires review of source Space geometry, boundary normals, wall clipping/space volumes, stable identities, rehosting existing relation surfaces and preservation checks. Do not infer “all 36 supported” or even official success for this one task.

Files: `src/runtime/topology_ops.py`, `src/runtime/compiler.py`, `tests/test_native_t_path_junction.py`, `tools/verify_real_t_path_pair.py`, this report and JSON evidence. Earlier stacked parent PR #69 provides the standalone wall geometry manual oracle. No modifications to normative Xim/BIXML or original IFCS.
