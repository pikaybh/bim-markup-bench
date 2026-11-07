# G1 #11 — Real IFC read-only projection and no-op integrity audit

**Status: PARTIAL ACCEPTANCE, issue remains OPEN until class coverage and model-information parity are verified.** This is not an IFC edit compiler or a self-contained lossless BIXML native document.

## Pinned reproducible environment

- macOS arm64, Python 3.12.13, IfcOpenShell 0.8.4.post1, lxml 6.0.2 (uv.lock).
- Self-authored IFC4X3 fixtures: tests/fixtures/synthetic/input.ifc, expected_wall_height.ifc, expected_window_move.ifc.
- One real BIM-Edit IFC input: pinned model revision 0ae510bd21865def4e2c6145c1244f01a1e3bcb9, simple/17_input.ifc (15,313 bytes). Local copy and all other dataset inputs are ignored by Git.
- 4.31GB official IFC corpus was NOT downloaded.

## Observed coverage

| IFC class | Synthetic tiny IFC | Actual tiny BIM-Edit sample | Status for general 324 |
| --- | --- | --- | --- |
| IfcBuildingStorey | 1 / 1 projected | 2 / 2 projected | Other storey variants unverified |
| IfcWall | 1 / 1 projected | 5 / 5 projected | Simple straight rectangular swept solids and explicit axis only |
| IfcSlab | 1 / 1 projected | Not present | Rectangular axis-aligned extrusion only |
| IfcColumn | 1 / 1 projected | Not present | Rectangular axis-aligned extrusion only |
| IfcSpace | 0 / 1 managed, 1 explicit opaque | Not present | **BLOCKED** where IfcSpace geometry is missing or unsupported; 72 BIM-Edit tasks target this class |
| IfcOpeningElement | 2 / 2 projected | Not present | Unique supported wall host + rectangle void only |
| IfcWindow | 1 / 1 projected | Not present | Unique supported opening fill; OverallWidth/Height provided |
| IfcDoor | 1 / 1 projected | Not present | Unique supported opening fill; OverallWidth/Height provided |

The self-generated IfcSpace has identity, storey and a space boundary **but no geometric representation**, so its dimensions cannot legitimately be invented. It stays explicitly opaque in a backend-only ledger along with the boundary. Strict projection therefore correctly refuses the synthetic fixture. This is a deliberate scientific limitation; it must not be counted as a successful IfcSpace benchmark solution.

The real BIM-Edit small input contains five Revit-style walls using both Curve2D and SweptSolid, two IfcBuildingStorey instances and five wall connections. These were projected into schema-valid declarative XML, including stable local ID and genuine source IFC GlobalId. The single dataset sample is insufficient to claim full dataset coverage.

## Source preservation evidence

- src/runtime/ifc_snapshot.py computes immutable input byte SHA-256, every original STEP entity text fingerprint, all GlobalIds and known explicit relation endpoint sets.
- src/runtime/ifc_projection.py creates a **managed XML subset** with sourceModelSha256 pin. Omitted entities, property sets, material records, geometry details and unsupported relations remain **unaltered in the original IFC**; they are not magically encoded into XML.
- Exact unchanged state can be passed through using passthrough_noop: copy the pinned IFC to a separate new file, reparse, compare byte SHA-256, STEP entity graph digest, GlobalIds and relation memberships. It refuses all actual XML state edits (create/update/delete) rather than pretending to compile them.
- No overwrite of original source or existing output; checksum mismatch, mutated source, invalid host, or unsupported geometry fails closed.
- Independent Pset test: changing FireRating from F120 to F60 changes graph fingerprint, while a no-op IFC copy preserves it.
- The projection never opens ground-truth IFC or scorer annotations, and the XML contains only editable source entities (some legitimate existing IFC GlobalIds), not benchmark target annotations.

## Reproduction

    uv sync --frozen --python 3.12
    .venv/bin/python -m tools.project_ifc tests/fixtures/synthetic/input.ifc --xml-out data/projections/building.xml
    .venv/bin/python -m tools.validate_markup data/projections/building.xml
    .venv/bin/python -m unittest tests.test_ifc_projection -v
    .venv/bin/python -m unittest discover -s tests -v

For output byte-for-byte no-op comparison, use a new unique output path and --noop-copy data/projections/unchanged.ifc; the command refuses to replace existing files. The CLI output is a backend audit summary; do not expose hidden GT, proprietary IFC, key or per-file rights metadata to an agent.

## Still missing before Issue #11 can close

1. Verify projections on a preregistered, representative set covering all 6 IFC classes and direct/spatial/topological operations across real BIM-Edit IFC. Current sample only demonstrates straightforward walls.
2. Add a **truthful** IfcSpace representation and spatial graph boundary handling; preserve/material/complex geometry and avoid unsupported silent drops.
3. Establish matched information exposure for direct XML and Python baseline. The Python arm currently may read more raw model detail than the direct-markup arm. This is a research validity gate.
4. Build real typed stable binding and transactional IFC **edit** compiler (#12/#13), then verify no-op against genuinely compiled model rather than byte-preserving input copy only. The current no-op proves preservation, not edit correctness.
5. Audit and checksum the remaining licensed model corpus (Issue #3) and independent evaluator (Issue #4/#21).

Do not report a benchmark pass rate or claim full IFC edit support from the no-op integrity test.
