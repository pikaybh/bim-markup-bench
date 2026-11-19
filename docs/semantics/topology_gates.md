# G1-07 / Issue #15 — bounded, actual IFC hosted and wall topology edits

**Status: PARTIAL — Issue #15 must remain OPEN.** The direct-edit model reads
and changes declarative XML ONLY. A separate trusted compiler derives and
preflights a typed graph diff, updates the copied IFC4X3, and independently
verifies actual native IFC relationships and placements.

## Supported topology delta

| XML edit | IFC effect, inspected after reimport | safety / rejection |
| --- | --- | --- |
| Delete an existing Window node, retain hosted Opening | Removes exactly one IfcWindow and its IfcRelFillsElement. Keeps IfcRelVoidsElement, IfcOpeningElement, IfcWall, unrelated fills and spatial relationships | Only if filling has precisely one host and no material, Pset/type, group or other IFC inverse dependencies |
| Delete a **uniquely preflighted Door+Opening pair** by removing both state nodes | Removes both IfcProducts, their Fill/Void, the dependent Door-only SpaceBoundary, owned Psets/material, and only the Door's shared Type/Classification/Storey membership; host physical void closes | Only a single isolated paired state diff and the exact source-native inverse classes/ownership observed and specified in docs/gates/G1_public_door_delete_compiler_v02_20261111.md; any unknown dependency blocks atomically. **Not a general IFC Space/Room boundary regeneration policy or official scored task.** |
| Change an existing Opening offset | Adjust only the opening's local IfcCartesianPoint; child window/door placed relative to opening moves with it, exact fill and void GUIDs retained | No tilt, unsupported world rotation, non-native child placement, wall-void collision, unbound host or boundary dependencies |
| Add a Connects relation | Generates a stable derived IfcRelConnectsElements with correct source/target native Wall GUIDs | Two typed walls, same storey, physically meeting endpoints, not already connected, no new GUID collision |
| Remove existing Connects | Deletes only specified IfcRelConnectsElements | Existing exact native directional connection with no ConnectionGeometry |
| Create two standalone walls and connect them in one XML document | Creates two geometrically real IfcWall objects, their storey containment, then connects their endpoints | All new Wall geometry and IDs validated, transaction staging rolls back as a unit |

These changes are applied only to a separate private cloned IFC model,
never to the source file. Every result is independently reopened; native
IfcRelContainedInSpatialStructure, IfcRelAggregates, IfcRelVoidsElement,
IfcRelFillsElement, IfcRelSpaceBoundary and IfcRelConnectsElements
relationships are compared. An unintended relation, host, fill or shared
storey membership change aborts the IFC output stage.

For Opening-only translation, **every original STEP entity** must survive,
with *only* the approved placement IfcCartesianPoint modified. It is not
enough to see the correct XML offset; the native filling world transform
must move by exactly the requested offset and all relation GUIDs must persist.

## Known limitations (engine coverage, not LLM failures)

- IfcSpace in the self-authored source IFC exists with an IfcRelSpaceBoundary
  marked PHYSICAL/INTERNAL, but lacks an IfcSpace shape representation. Its
  source relationship remains immutable/opaque; no boundary editing or
  orientation normalization is currently supported.
- Native wall rotation / curved and non-axis-aligned host frames are rejected;
  a universal world frame/inverse-placement solver is not claimed.
- IfcRelVoidsElement with a changed width/height, resizing a window/door,
  creating an Opening or Window, deleting a lone Opening/Wall with dependencies,
  or adding a SpaceBoundary is not implemented. The new paired Door+Opening
  deletion is only supported under its separately versioned narrow native
  source dependency policy, not arbitrary host deletes.
- Complex wall joins with ConnectionGeometry, wall geometry repairs, material
  and Pset cascades, overlapping openings and multi-floor associations are
  not supported.
- A generated IFC's file bytes may cause a new XML local ID on reprojection.
  IFC GlobalId remains stable but author-selected local ID continuity still
  needs explicit persisted mapping (#12/#13).
- No full BIM-Edit 324 scoring. These are deterministic native IFC functionality
  tests on own small fixture(s), not model trials.

## Tests and independent evidence

    uv sync --frozen --python 3.12
    .venv/bin/python -m unittest tests.test_topology_edits -v
    .venv/bin/python -m unittest discover -s tests -v

The test module verifies three representative positive topology changes and
additional failures: deleting a filled Window, moving a hosted Opening,
creating/deleting a real wall-to-wall connection; nonmeeting endpoints,
duplicated connections, invalid host, overlapping voids and type/Pset
dependent deletion refusal. Native IFC4X3 relationships and real world
object placements are checked after export/reopen; XML alone cannot pass.
No paid model API calls, no hidden answer data and no BIMXL/Xim edits occur.
