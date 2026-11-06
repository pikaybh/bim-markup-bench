# Test XML examples

- valid/basic_building.xml: well-formed v0.1 building state (wall, slab, column, space, hosted opening, window, door, physical space boundary).
- invalid/command_list.xml: imperative wrapper action forbidden.
- invalid/duplicate_id.xml: repeated stable XML id forbidden.
- invalid/missing_host.xml: Opening.host references absent/wrong-class Wall and must fail.
- invalid/negative_dimension.xml: negative thickness is forbidden by XSD.

The sourceModelSha256 in these example files is intentionally 64 zeroes as a **demo placeholder**, not the hash of an actual IFC. A real IFC compiler MUST compare the attribute to the local immutable input asset hash and reject it unless it matches. These examples are not model edits, scored benchmark outputs or valid target source files for real IFC models.

Example schema check on macOS:

  xmllint --nonet --noout --schema spec/toy_markup_v0.xsd examples/valid/basic_building.xml

XSD validation alone does not verify geometric surfaces, IFC relation topology, dynamic loads or signed binaries; separate G1/G2 tests are required.
