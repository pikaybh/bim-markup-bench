# IFC-to-XML read projection ABI and irreversible editing boundaries

The LLM can see and edit **declarative XML only**. A trusted offline source projector may use IfcOpenShell as an implementation detail. This is not permission for the direct XML LLM to call BIM APIs.

- Source IFC: immutable backing binary, exact SHA-256 pinned.
- Projected XML: strict v0.1 object definitions for verified simple geometry and type-safe references. Every managed existing entity retains its genuine IfcGlobalId; the human-readable local ID is a deterministic hash-derived name.
- Opaque ledger: every unmanageable IFC product and incomplete space/host relation is reported **separately on the backend** as unsupported/opaque by IFC class and GlobalId. The system does not create fictional geometry. Omitted source entities survive the no-op path bit-for-bit.
- Unsupported source model input must not be silently treated as fully editable; v0.1 supports IFC4X3 in meters only, verified straight walls, axis-aligned solids, hosted rectangular voids/fillings and selected relation endpoints.
- IFC spatial graph/host bindings that depend on unrepresented IfcSpace must be marked incomplete. A model may have valid IFC entities without enough geometric data for this toy XML grammar.
- No-op is an exclusive, byte-preserving file copy after parsed source-state equivalence and source content checksum verification. It is NOT a general XML→IFC compiler.
- Any actual XML edit currently returns an error instead of a plausible-but-incorrect IFC output.
- A future compiler (#13) will clone the original IFC and apply typed semantic delta with source GlobalId conservation and IFC schema/relation correctness; it must add independent result validation and transactional rollback.
- Hidden ground truth, target IDs, grading metadata, API keys and private file paths are never model-visible. Existing source GlobalIds of projected entities are legitimate model input information rather than task answer annotations.
- The Python control arm must be restricted or the direct XML arm given corresponding projected context under a recorded equivalence test (#17/#18); parity is not yet established.

This is an experimental IFC-backed overlay, **not** a native standalone BIMXL/BIXML document, Revit equivalent, or general six-class BIM-Edit solution.
