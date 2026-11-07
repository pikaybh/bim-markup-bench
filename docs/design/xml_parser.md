# #10 — Safe v0.1 XML parser and typed AST

This module is a **trusted, offline, non-mutating parser** of the experimental
declarative XML language. It is not the BIM-Edit benchmark runner, an IFC compiler,
the G1 semantic binding engine, an agent tool, or a full security boundary for
arbitrary generated Python.

## Installation / isolated checks

From this repository with uv 0.8.5 and Python 3.12:

    uv sync --frozen --python 3.12
    .venv/bin/python -m tools.validate_markup examples/valid/basic_building.xml
    .venv/bin/python -m tools.validate_markup examples/invalid/negative_dimension.xml
    .venv/bin/python -m unittest discover -s tests -v

The first validator command exits 0 and reports
VALID_DECLARATIVE_XML_ONLY, while the second exits 2 and emits a
machine-readable diagnostic. The placeholder sourceModelSha256 in the valid
example is 64 zeroes and is **not** authenticated against an IFC file. Pass
--expected-source-sha256 with a trusted external IFC file digest when operating
on an actual projected document.

## Input security and integrity

The parser uses an immutable local XSD and lxml 6.0.2, with DTD/entity
declarations, external resolution, network schema imports, and huge XML
trees prohibited. Expat first enforces a **2 MiB** raw byte cap, a maximum of
**96 nesting levels**, **4096 elements**, **32 attributes per element** and
a **16 KiB start-tag** cap. Both the Expat source-position pass and the lxml
structure pass have to agree.

The parser maps to an immutable, typed BuildingDocument:
- Typed Decimal attributes, stable local IDs and optional IFC GlobalIds
- root and element SourceSpan with absolute opening-tag byte offsets and
  one-based source file line/character columns
- Complete immutable original XML bytes including comments and whitespace
- Exact source byte SHA-256 and semantic document SHA-256
- immutable sourceModelSha256 binding, validated against a provided expected
  SHA-256 when supplied

Machine-readable diagnostics use a closed schema, with a code, severity,
sanitized basename, one-based line/column and best-effort element ID. The
most important limitations: for an XML schema error the reported column is
best effort, and the opening tag span does not cover the full element body;
no byte-perfect XML patcher is implemented yet. Full lexical ownership and
roundtrip source patch generation belong to later G1 work.

## Semantic diff, zero mutation

The pure semantic_diff function compares previous and edited snapshots,
identifying created, modified and deleted **managed** local nodes and changed
declarative relation sets. It refuses a modified immutable source hash, IFC
schema, element kind or existing IFC GlobalId. Reordering, comments, XML
attribute ordering, whitespace and equivalent decimal representations such
as 0.20 and 0.2 produce no semantic change. It emits an in-memory change
plan only; it **does not** write or delete any IFC entity.

try_parse_update retains the exact previous validated BuildingDocument and
its source bytes when partial/invalid XML is saved. Because no compiler is
present, no result.ifc output is created by the parser; preservation of
a last-valid **IFC output** is a future transactional compiler acceptance
criterion (#13/#16).

## Safety boundaries remaining

This parser is not a process sandbox. The future Python control arm needs OS
sandboxing/network isolation (#19). Geometry/topology, IFC GlobalId mapping
and staged output are not computed here (#11–#16). Source secret redaction
protects common key patterns but must never substitute for removing secrets
from model contexts and filesystem mounts altogether.

Tests cover schema rejection, DTD/XXE, nested/oversized documents, malformed
partial edits, source positions, unicode, stable identity, semantic diff,
numeric normalization and invalid host refs. The benchmark corpus and OpenAI
key are not read by these commands.
