# G1 #15 — Door deletion, retained IFC SpaceBoundary footprint geometry

**2026-11-11 KST · Source-only native IFC4X3 inspection.**

**Result:** PASS_PLANAR_WALL_BOUNDARY_RINGS_FULL_3D_SHELL_UNVERIFIED.

**Research release gate:** BLOCKED. This is a new, post-hoc, narrowly
developed **2D perimeter certificate**, not a full BIM-Edit author metric
or a generally valid 3D IfcSpaceBoundary shell check.

## 1. Critical correction to the previous inference

The previously observed IfcRelSpaceBoundary count reduction from 12 to 11
is NOT evidence that the horizontal Room wall perimeter opened. In the
immutable source IFC, each Room has **four existing external first-level
vertical Wall boundary surfaces**, forming a closed rectangle in plan.
The targeted Door boundary is **an auxiliary patch lying exactly on top
of one existing Wall perimeter segment**, not a replacement perimeter
edge. It is removed together with its Door by the native IFC cascade.
The four Wall perimeter segments are unchanged.

The IFC file has two original IfcSpace objects. The first has area
83.0000 m2 and full Wall perimeter length 36.6000 m; the second has
area 65.0000 m2 and full Wall perimeter length 33.0000 m. All eight
Wall boundary surfaces extrude vertically through 3.048 m.

Source Room with 83 m2 perimeter:
- Wall-boundary segments 4 before and 4 after.
- Auxiliary Door/Window boundary patches 2 before and 2 after.
- All original Wall segment endpoint coordinates, vertical extrusion
  heights and surface signatures preserved.

Source Room with 65 m2 perimeter (the Door deletion occurs here):
- Wall-boundary segments 4 before and 4 after.
- Auxiliary Door boundary patches **2 before and 1 after**.
- The deleted Door patch overlays an unmodified Wall boundary segment.
- Original four Wall segments still form one simple, closed connected
  XY loop of perimeter 33 m and planar area 65 m2.

Thus **the 2D Wall-boundary footprint remains closed** and no detached
endpoint is introduced by deleting this Door's auxiliary patch.

However, *full three-dimensional IfcRelSpaceBoundary shell closure is
NOT proven*. The first-level boundary collection in this IFC does not
supply an explicit floor and ceiling IfcRelSpaceBoundary pair for each
Room. The preserved IfcSpace physical shape is not interchangeable
with independently validated face-to-face oriented IFC spatial
boundary topology. No floor/ceiling reconciliation was attempted.

## 2. What the new trusted validator actually proves

New runtime-only module:
src/runtime/space_boundary_footprint.py

This validator reads the native IFC model, not XML claims or grading fields.
It supports only the actual bounded source's geometric relationship type:

- IfcRelSpaceBoundary, Name=1stLevel, PHYSICAL / EXTERNAL,
  one IfcConnectionSurfaceGeometry with a SurfaceOnRelatingElement
  of IfcSurfaceOfLinearExtrusion;
- each swept curve is IfcArbitraryOpenProfileDef containing one
  two-point IfcPolyline, with a finite vertical extrusion and rigid
  3D Axis2Placement transform;
- full-height Wall-sourced boundary segments must form a single
  simple, connected, non-zero-area closed XY polygon; endpoints
  have degree 2 and the extrusion depths/Z bases are consistent;
- Door and Window boundary patches must lie on existing Wall segments
  and fit inside the Wall's vertical extent;
- before/after space identities, Wall boundary GlobalIds, planar
  segment coordinates, vertical heights, areas and perimeters are
  unchanged. Only the explicitly identified target Door boundary
  may disappear; other Door/Window boundary surfaces must be identical.

Unknown surface subclasses, extra dependency variants, broken
perimeters, wrongly mapped Room boundaries or spatial nonfinite data
fail closed. This code is used inside the trusted backend only, after
the Door+Opening native IFC result has been staged. The earlier
IfcRoot-inventory and world-mesh validator remains in place.
A boundary-geometry error now aborts atomic publication, leaving no
partial IFC or staged-file residue.

**Important limitation:** the certificate tests a **2D perimeter**,
not full oriented, watertight 3D Room volume closure. It also does not
establish alignment with the author's hidden BIM-Edit evaluator or
resolve the absence of an original direct Opening -> Storey relation.

## 3. D0/I0 source-only cross-check and negatives

The fixed public candidate remains DOR-DEL-DIR-A-001. It uses
only its public instruction and the pinned input IFC:

- Source IFC SHA-256:
  170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb
- Published instruction SHA-256:
  8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a

The old v0.1 inability and the v0.2 newly supported narrow native
delete remain separate immutable historical evidence. This new v0.3
report adds a **native SpaceBoundary geometry postcondition** to the
same fixed source-only developer-authored D0 and I0 results.

The new trusted optional observer in
tools/verify_public_door_delete_gate.py reads each temporary result
before deletion; its **default v0.2 behavior is unchanged**. The new
tools/verify_public_door_space_footprint.py checks that D0 and I0
obtain the same two closed 2D footprints and identical unmodified
SpaceBoundary signatures. It stores only counts, areas, perimeters,
source/output hashes and explicit negative caveats in a sanitized
write-once report.

New negative tests cover:
- deletion of an unrelated Wall boundary relation;
- an underlying IfcPolyline boundary endpoint moved off the ring
  (undetectable by a root-ID-only verifier);
- nonvertical surface extrusion / inconsistent Wall heights;
- a retained Door boundary moved off the Wall ring;
- a Wall boundary associated with the wrong native IfcSpace;
- a fabricated additional native Door boundary record;
- forced validator failure demonstrating no output or staging artifact.

The new postcondition does not alter any XML authoring API, original
IFC source bytes, frozen 36-case population, hidden reference, independent
scoring formula, provider budget, or Xim/BIXML product tree.

## 4. Reproducible execution (Windows pinned environment)

    $env:PYTHONUTF8='1'
    .\.venv\Scripts\python.exe -m unittest tests.test_space_boundary_footprint -v
    .\.venv\Scripts\python.exe -m tools.verify_public_door_space_footprint --output-json reports/g1_public_door_2d_space_boundary_footprint_20261111.json
    .\.venv\Scripts\python.exe -m unittest discover -s tests -q

Evidence JSON:
reports/g1_public_door_2d_space_boundary_footprint_20261111.json

Evidence SHA-256:
cc26cf3b441b9b4302487ba6f7c94fd4ad91bd69dee11b85cafc8b77c92d60a7

The CLI returns **exit 2 intentionally** even if the XY perimeter
passes. The G1/G2/G3 experiment release remains blocked by the
unverified official evaluator, GT protocol, asset rights and matched
model sandbox/provider configuration.

## 5. Scientific verdict and next question

**Supported:** original and deleted-output Wall boundary **XY rings**
are closed, their line/surface geometry remains unchanged, the one
deleted Door's patch had overlaid a retained Wall segment, and the
native IFC result does not acquire an obvious planar perimeter gap.

**Not supported:** an officially correct 3D Room boundary shell,
proper floor/ceiling boundary records, a complete oriented BRep
space-solid, alternative IFC semantics acceptable to the authors'
unknown grader, all task-class CRUD coverage, or any LLM performance
advantage of declarative XML over Python.

Next distinct work should determine, from the *public* benchmark
protocol or an explicit independently frozen geometry acceptance rule,
whether the 3D spatial shell / first-level boundary behavior must be
reconstructed at all. Never infer that requirement from hidden GT,
and never silently count unsupported Shell as task success.


### Supplementary native IfcSpace shape observation (not a boundary-shell certificate)

A separate source-only IfcOpenShell mesh probe of both original IfcSpace
SweptSolid representations found **8 mesh vertices, 12 triangles and 18
undirected edges per Room**. Every edge is incident to exactly two
oppositely directed triangles. Manually summing the signed tetrahedral
triangle volumes gives **252.984 m3** and **198.120 m3**, matching the
rectangular world-space Room bbox volumes. Existing native D0/I0 deletion
postconditions independently require the IfcSpace object meshes to
remain unchanged. These observations support closed original *product
shape meshes*; they do **not** supply the absent floor/ceiling
IfcRelSpaceBoundary relation faces or establish their oriented mating.
