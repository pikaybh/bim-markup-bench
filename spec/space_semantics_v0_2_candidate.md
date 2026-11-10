# Space Semantics v0.2 Candidate — EXPERIMENTAL, NOT PROMOTED

This is a **separately versioned research candidate**, not a change to
`toy_markup_v0.1.xsd`, the preregistered frozen sample, or the actual LLM
arm's authorized input/authoring API. This candidate is **read-only source
observation**, not a native Xim/BIXML schema or a lossless IFC serialisation.

## Motivation

The existing toy XML v0.1 exposes spatial geometry and limited
`SpaceBoundary` relationships but **omits the source IfcSpaceType,
IfcRelDefinesByType, IfcPropertySet and instance-specific properties**.
That means a correct/incorrect natural-language change to one room cannot
be adequately interpreted from only the projected XML source where
room-specific `Reference` or type semantics matter.

For the one frozen public input verified so far, the original IFC contains
two real `IfcSpace` objects with two distinct `IfcSpaceType` relationships
and four instance Pset relationships. Four `Reference` values include the
existing room's unique label. Neither the number of rooms nor these
relationships justifies automatically copying a room name, type/number or
Reference to a newly created room.

## Candidate markup

The proposed *additional observation* is a separate
`SpaceSemantics` XML document with namespace
`urn:bim-markup-bench:space-semantics:v0.2-candidate`.
Each `Space` is keyed by the existing **native IFC GlobalId** and
the corresponding local ID from the frozen v0.1 projection.

The source-level snapshot includes only source-observed:

- Space `Name`, `LongName`, `PredefinedType`, `CompositionType`.
- Exact source `IfcRelDefinesByType` GUID, `IfcSpaceType` GUID,
  name and predefined type.
- Exact `IfcRelDefinesByProperties` GUID, `IfcPropertySet` GUID and
  Pset name.
- Explicit `IfcPropertySingleValue` types and values
  (`IfcIdentifier`, `IfcLabel`, `IfcText`, `IfcBoolean`,
  `IfcInteger`, `IfcReal`), with no ambiguity in Boolean representation.
- `Quantities status="NONE_IN_SOURCE"` ONLY when there is no source
  `IfcElementQuantity`; a source requiring QTO reconciliation is **rejected**.

These are **observed source facts**, never guessed new-room metadata. If
native information cannot be represented exactly (unprojected Space,
source Space with unsupported attributes, complex or shared property,
unit-bearing value, type-level property set, independent QTO, etc.),
the candidate projector fails closed.

The v0.2 XSD is kept separately in
`spec/space_semantics_v0_2_candidate.xsd`, with fixed namespace, version,
source input SHA-256, source-only status and no executable commands or
arbitrary XML structure. The independent trusted source verification
reopens the public IFC, validates the candidate against its local XSD and
checks every original metadata value/relationship for equality. Forged
references, new fake Space GUIDs, stale source digests, fake QTO and
XML DTD/XXE attempts are rejected.

This profile **does not authorize the model to edit Space semantics or
create new native SpaceType/Pset/quantity relationships**. A future,
separately reviewed write-capable schema must require source-supported,
explicit and unique room number/name/type/ref/quantity semantics and
demonstrate independent D0/I0 IFC parity before experimental promotion.

## Paired model input protocol is NOT changed

The audit `tools/audit_space_semantics_v02_pair.py`:

1. Builds a v0.1 direct-XML observation from the real G2 source-only runner.
2. Builds a v0.1 imperative-control observation from the same public IFC.
3. Independently materializes two proposed v0.2 source semantic overlays.
4. Requires all common task instructions, source IFC SHA, v0.1 XML/spec
   bytes and the v0.2 candidate bytes to be identical.
5. Records **SHA-256 hashes and counts only**, not a copy of source IFC
   or room-specific metadata in Git.
6. Explicitly reports `model_facing_v02_enabled=false`,
   `input_fairness_and_model_budget_approved=false`,
   `new_space_type_pset_qto_authoring_compiler_implemented=false`.

Thus, this establishes reproducible **symmetric candidate
materialization**, not a run with model-visible candidate inputs, nor
complete semantic-input parity for all IFC. The imperative code tool
reference and direct XML edit authoring capability are treatment-specific
and still different.

## Frozen-input source-only evidence

Task `WAL-CRE-SPA-A-003`, original public input IFC SHA-256:

`e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`

| Independent fact | Observation |
|---|---:|
| Original projected IfcSpace objects | 2 |
| Source IfcSpaceType relations | 2 |
| Source instance Pset relations | 4 |
| Source `Reference` properties | 4 |
| Baseline v0.1 XML bytes | 2684 |
| Proposed source metadata XML bytes | 2211 |
| D/I candidate bytes equal | Yes |
| Source IFC read back without mutation | Yes |
| v0.1 parser/schema/compiler changed | **No** |
| Model inference / paid calls | 0 |
| Official benchmark tasks scored | 0 |
| Official evaluator called | No |

Structured evidence:
`reports/manual_space_semantics_v02_candidate_20261110.json`.

## Repeatable local tests

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_space_semantics_v02_candidate tests.test_space_semantics_v02_pair -v
.\.venv\Scripts\python.exe -m tools.audit_space_semantics_v02_pair
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The report CLI intentionally exits **2** because a viable input
*candidate* is not an approved fair/LLM/official evaluation. The fixed
36-task sample, scorer contracts, original IFC bytes, V0.1 vocabulary and
production BIXML/Xim repositories remain unchanged.

## Required review before protocol promotion

A new experimental phase must predefine source/context versioning,
possible token-context overhead, model visibility of direct vs imperative
tools, whether the metadata overlay is editable declarative state or
read-only, stable type/reference/quantity identity semantics and the
native IFC mutation contract. If a different grammar is compared to
original v0.1 it is a **versioned ablation**, not a silent improvement to
the preregistered original experiment. Explicit paid inference, OS
sandbox and official evaluator verification remain separate gates.
