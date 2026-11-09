# G1 #11 — Exact world-axis-aligned IFC Space cuboid projection (2026-11-09)

**Scope:** trustworthy IFC4X3 → declarative XML read-only projection; additive partial support only. Source asset is a locally cached, byte-hash-pinned **public INPUT** for frozen BIM-Edit task `WAL-CRE-SPA-A-003`. No reference/GT file opened.

## Baseline and underlying error

The referenced source IfcSpace previously remained opaque with `Rotated swept extrusion frame unsupported` even though the actual native world mesh has precisely eight vertices at the corners of an axis-aligned cuboid and twelve triangles covering its six rectangular faces.

The room's world bounding cuboid is:
- min (x,y,z) = (0.175, 2.900, 0.000) m
- spans (width,depth,height) = (4.450, 3.125, 2.800) m.

In the frozen task, both the directly editable XML context and the imperative Python/IfcOpenShell context must be provided enough visible source geometry to reason about which room and door are referenced. Omitting a room from D's XML while I can open the full source IFC is a material information asymmetry.

## Narrow implementation

`src/runtime/ifc_projection.py` now uses a fallback for IfcSpace **only** when a valid rectangular native swept-solid exists but the source's internal orientation is not a world-aligned frame. The fallback reads real IfcOpenShell world-coordinate triangles and requires:

1. Exactly eight native vertices, twelve nondegenerate triangles, finite reasonable extents and eight expected world box corners.
2. Exactly two triangles on each of the six axis-aligned faces, spanning four corners with aggregate area equal to the full rectangular face.
3. Consistent level association and the existing typed declarative Space XML fields. Non-Space elements, non-rectangular sweeps, tilted extrusion directions and missing geometry remain outside this fallback.

This deliberately rejects arbitrary oriented volumes instead of silently substituting a misleading bounding box.

## Verification

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_space_world_cuboid_projection tests.test_ifc_projection -v
```

**14 tests passed**, including:
- previously opaque frozen task Space is now present as a properly dimensioned XML `Space`;
- mutated copy with oblique 45° swept profile remains opaque, never misrepresented as an AABB;
- unchanged XML compiled to IFC yields byte-for-byte identical pinned input file;
- existing synthetic and native projection guards unchanged.

## Limits / disclosure

This verifies *axis-aligned box geometric context*; it does not expose arbitrary IFC geometry, solve subjective viewpoint references, establish all physical/spatial topological relationships in XML, or score an official task. The IFC input is still the immutable authoritative model; declarative XML is an IFC-backed partial projection. No IFC input/GT files are added to git. No LLM calls, new external corpus downloads, official scorer runs or Xim/BIXML changes.

This change unblocks re-running the **manual** source-only spatial wall geometry oracle on separate Issue #14, without claiming an LLM success or official BIM-Edit score.
