# Reviewed minimal IfcOpenShell imperative control reference

This is a backend API reference for the imperative Python arm, not a
solution to any experimental task. Both arms receive the same source IFC
projection and natural-language task, but only the imperative arm is
allowed to generate IfcOpenShell authoring code in solution.py.

- import ifcopenshell
- import ifcopenshell.api.root, ifcopenshell.api.geometry,
  ifcopenshell.api.spatial
- model = ifcopenshell.open('input.ifc') — input must be read-only.
- Products are selected by verified IFC GlobalId.
- For safe wall creation: IfcWall, Body subcontext, representation, explicit
  placement, storey containment.
- An IfcOpeningElement's IfcRelVoidsElement attaches it to host Wall;
  an IfcRelFillsElement attaches a Window/Door to Opening.
- IfcRelConnectsElements records native wall relationships.
- Write only to fresh result.ifc within a future isolated task workspace.

Actual code execution is intentionally disabled before sandbox #19.
No pretrained oracle solution snippets, benchmark target GUIDs or secret
reference outputs are included.
