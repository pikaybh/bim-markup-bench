# Source authority and mutation rules

1. Immutable input.ifc is a content-addressed substrate (sourceModelSha256).
2. building.xml is the LLM-editable authoritative *managed projection*, not the entire IFC document.
3. Trusted runtime parses/validates building.xml and binds local IDs to IFC GlobalIds.
4. Internal semantic graph and IFC delta are **derived** from a valid XML version and the original input IFC. No second hidden writeable model state is authoritative.
5. last_valid XML snapshot + corresponding output IFC are kept until the next complete source validation and atomic file replacement succeed.
6. Unmanaged IFC entities/relationships always pass through unchanged; removing unrepresented data is forbidden.
7. On incorrect host IDs, unsupported class, invalid geometry or hidden-output leakage the compiler refuses to commit, preserving the last valid output.
8. GUI authoring and source-preserving reverse edits are out of scope for the experiment until explicitly tested.
9. The LLM sees only declarative XML file and language notes; IfcOpenShell API may be used **behind** the runtime boundary but not by the model in the direct markup arm.
10. Dataset task reference IFC, hidden target GUIDs and evaluator remain exclusively grader-side.

This is an experimental interface contract, not a production BIMXL/BIXML schema.
