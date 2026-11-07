# Toy Declarative BIM Markup v0.1 — research-only language contract

**Status: experimental syntax, NOT BIXML/BIMXL normative schema or Xim API.** The purpose is to isolate whether an LLM can reason over and edit a human-readable building *state* more reliably than writing Python/IfcOpenShell programs. The direct-edit model never writes commands or invokes BIM mutation tools.

## Model

The document root is Building in the unique namespace urn:bim-markup-bench:toy:v0, version 0.1.

It has ordered sections (Levels, Elements, optional Relations). The root records sourceModelSha256 as exact lowercase 64-byte hex, units fixed to m, and ifcSchema fixed to IFC4X3. This is a **prototype IFC-backed representation**: the immutable source IFC remains an external protected substrate, and XML is authoritative only for the nodes/relationships explicitly included in its managed projection. Unrepresented IFC entities are opaque passthrough and must not be changed.

State nodes:
- Level: id, optional ifcGuid, elevation (global storey offset m).
- Wall: id, optional ifcGuid, level ID, Cartesian endpoints x1,y1,z1 and x2,y2,z2 in the level frame, height, thickness.
- Slab: rectangular MVP with id, optional ifcGuid, level, x/y/z, width, depth, thickness.
- Column: rectangular prism with level, local origin x/y/z, width, depth, height.
- Space: rectangular volume with level, local origin x/y/z, width, depth, height; IFC native IfcSpace identity, NOT a decorative room label.
- Opening: hosted on an existing declarative Wall via host ID, local offset measured along the Wall axis, sill, width, height. This MUST become a real void in host shape.
- Window / Door: fills an Opening via opening ID, width and height. Host wall relationship is induced, not serialized as procedural add_filling calls.
- Relations/SpaceBoundary: space ID and wall element ID, kind fixed PHYSICAL in initial schema.
- Relations/Connects: source and target Wall IDs, an IFC structural connection to be validated by the backend.

In v0.1 all dimensions, world/level offsets and lengths are SI **meters** with lexical decimal numbers; XSD enforces strictly positive dimensions and nonnegative sill. The XSD does not enforce geometric nonintersection, host window width <= wall length or actual clash/space boundaries. Those belong to semantic binder/geometry engine (#12/#14/#15). No arbitrary expression language, include directives, executable Python, transform scripts or external fetches exist in the vocabulary.

## IDs and edit operations

- Local id is an XML xs:ID, stable across text edits, namespace-wide unique.
- ifcGuid is optional on a newly declared object; existing projected IFC entities must retain their original 22-character IFC GlobalId. A new object must receive a stable derived/computed IFC GlobalId before IFC export (exact allocation/failure on collisions is a G1 #12/#13 ABI contract).
- **Create:** a new node appears relative to the previous valid declaration set; runtime constructs object and relations in an isolated IFC clone.
- **Update:** existing id appears with changed semantic properties or relationships; runtime computes diff. Reordering, indentation, harmless formatting and comment edits are not semantic changes.
- **Delete:** an element previously in the **managed XML snapshot** disappears; only that previously managed ID and explicitly owned relations may be deleted. Unrepresented IFC objects are NEVER deleted merely because they are absent in XML.
- **Relate:** changing a host/opening/SpaceBoundary/Connects reference changes the declarative graph; the runtime derives IFC relation delta and requires geometry/topology coherence.
- **No-op:** equivalent semantic snapshots preserve all existing IFC GlobalIds and unrelated Psets/materials/relationships.
- **All edits fail atomically:** invalid XML, malformed units, dangling/wrong-class references, geometry failures or unsupported schema must not overwrite last valid IFC output.
- **No imperative XML actions:** tags named Create, Update, Delete, Set, Move, AddWall, CreateWall, Execute etc are forbidden by the closed schema, including any arbitrary operation list.

## Projection and preservation

For each task, input IFC file must be immutable, pinned by sourceModelSha256 and unavailable to LLM mutation. The experiment runtime chooses and records which source entities are part of the managed XML projection **before** the LLM sees a task. It stores stable ID/IFC GlobalId mappings. On file edit, it compares last valid snapshot with new snapshot using stable IDs. Only those identified as managed in previous validated state can be candidates for deletion; unknown references to opaque IFC source entities must be allowed only if explicitly represented by a future formally typed external reference mechanism. That mechanism is *not* in the v0.1 schema.

Reference validation:
- Level owner references must identify Level objects.
- Opening.host must identify a Wall object.
- Window/Door.opening must identify an Opening.
- SpaceBoundary.space must identify Space and .element must identify Wall.
- Connects.from/to must identify Walls.
- Existing IfcGuid uniqueness and syntactic constraints required.
- The actual IFC exporter must validate IfcRelVoidsElement, IfcRelFillsElement, IfcRelContainedInSpatialStructure, IfcRelSpaceBoundary and IfcRelConnectsElements. Passing XSD alone is not proof.

## Canonicalization

The author edits the original text and the runtime should preserve comments/formatting for source Diff. For an *internal semantic fingerprint* the v0.1 prototype:
1. Rejects unsafe DTD/entity content before parsing (G0 #8 preliminary gate).
2. Parses XML tree, ignores comments and XML whitespace that is not data, sorts attributes deterministically.
3. Sorts siblings in Levels/Elements/Relations by element kind and stable ID (or stable attribute tuple for relations).
4. Emits a canonicalized semantic XML byte sequence and SHA-256 digest.

Code prototype: src/runtime/markup_normal_form.py. It does **not** replace the future robust typed parser and line/column preserving source map (#10), full semantic binder (#12), compiler (#13) or official benchmark evaluator (#21). The parser must enforce byte/depth/attribute quotas and no external entity processing.

## Deliberate limitations

- Geometry is limited to straight walls, rectangular slabs/columns/spaces and rectangular hosted openings.
- No profile polygons, orientation quaternion, slope, curve, family, MEP, constraints beyond typed links, native RVT/RFA, IFC2X3 or IFC4 support in v0.1.
- No instant GUI hot reload or bidirectional GUI editing yet.
- The input IFC model can contain omitted types/relations: the overlay is **not a self-contained lossless BIM native file**.
- Metadata/dimensions alone do not define true IFC geometry correctness. The compiler and an independent blind scorer must operate on actual IFC files.

## Validation and migration

Offline structural tests: xmllint --nonet --noout --schema spec/toy_markup_v0.xsd examples/valid/basic_building.xml.
Invalid cases in examples/invalid/ MUST fail. The library tests check semantic digest equivalence and malicious XML rejection independently from XSD.
Do not expand schema to raise benchmark success without preregistered version + test set. A future alternative grammar is a separate ablation experiment, not an unnoticed refactor.
