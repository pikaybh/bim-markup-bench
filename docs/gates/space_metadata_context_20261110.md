# G1 / Issue #15 — Native IfcSpace type/Pset/QTO preservation and D0/I0 source-context audit

**Date: 2026-11-10. Research status: CORE_TEXT_CONTEXT_EQUAL; NATIVE_SOURCE_METADATA_PRESERVED; FULL_SEMANTIC_INFORMATION_PARITY_BLOCKED.**

This document is a source-only scientific gate in the independent `bim-markup-bench` repository. It does **not** claim official BIM-Edit task success, completed type/Pset semantics for a new Space, an AI-authored solution, a successful matched LLM trial, or complete unambiguous support for the fixed 36-case candidate sample.

## Input and research constraint

Frozen public INPUT task `WAL-CRE-SPA-A-003`, verified IFC SHA-256:

`e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de`

The prior stacked Draft PR #72 created an independent deterministic paired oracle for one narrow native Wall/T-junction/IfcSpace split; D0 authored ordinary XML state and compiled it to IFC, and I0 independently authored IFC in Python/IfcOpenShell. **That native IFC geometry/connection parity is real**, but is not proof that all semantic information in IFC can be represented by the toy XML.

The current source-only inspection exposes a concrete issue: the target original `IfcSpace` has all of these relationships:

| Native source meaning | Grounded observation |
|---|---|
| Existing SpaceType relationship | Exactly **1** `IfcRelDefinesByType` to an `IfcSpaceType`; membership is unique to the existing room |
| Original instance Psets | Exactly **2** `IfcRelDefinesByProperties`: `Pset_SpaceCommon`, `Pset_SpaceHeaterTypeCommon` |
| Instance-specific identifiers | Both Psets include a `Reference` property tied to the original room identity |
| Other named attributes | Existing room has distinct `Name` and `LongName`; the type itself is named for that room |
| Geometry-linked `IfcElementQuantity` / QTO | **0** for the source room |
| IFC material/classification association | **0** for the source room |
| Other source IfcSpace | Also has type/Pset semantics, and must not be changed |

The model-facing toy XML projection omits the native `IfcSpaceType` and native Pset definitions. Therefore a model cannot independently reconstruct a new room's semantically correct type/room-number/Reference from these source declarations alone; neither arm should silently clone the original room's unique identifiers. Similarly, changing room geometry without recalculating an existing `IfcElementQuantity` would be unsafe.

## Implementation: explicit no-fabrication metadata policy

`src/runtime/space_metadata_gate.py` provides two **trusted backend** functions:

- `preflight_source_room_semantics`: before editing, validate IFC4X3, unique typed source, exact single-owner type and Pset memberships, simple non-ambiguous instance properties, no geometry-dependent `IfcElementQuantity` awaiting recalculation, and no unsupported material/classification links.
- `verify_native_space_metadata`: after native IFC generation, prove the original room's type/Pset relationship IDs, members and property values are preserved, other source spaces' metadata are preserved, and the new Space has **not** silently acquired copied type/Pset/QTO/material metadata without XML instructions.

The compile path in `src/runtime/space_partition_compiler.py` performs this preflight before native changes and validates the written IFC in the **staged output** before atomic file commit. A forged/shared room-specific Pset or source SpaceType is rejected. The compiler still supports the geometry-only bounded manual paired oracle but does **not** mark the new room semantically complete.

The policy deliberately rejects a source native `IfcElementQuantity` when quantity recalculation is not proven. It does **not** invent floor area, volume, room identities, occupancy values or Pset contents. An existing room's `Reference` is not cloned to the far room, and a new far `IfcSpaceType` is **not** fabricated.

Both separately authored IFC outputs (D0 XML runtime and I0 Python reference) were checked with this same **read-only audit** after authoring. The two metadata audit summaries match, and the previously established native-only IFC comparator still passes.

## Model-visible D/I source information audit

`tools/audit_space_metadata_context_parity.py` uses the existing *public task payload*, `stage_source_only_workspace`, and `create_matched_observations` to actually construct both model-facing contexts **without calling a model**.

The following **five shared source facts** match between D0 and I0:

1. Public task ID.
2. Public instruction string.
3. Projected XML source bytes.
4. XML language-specification bytes.
5. SHA-256 of the immutable input IFC.

This proves **core text-observation equality for this one input**, not full experiment parity. The I0 runner also provides a Python/IfcOpenShell API note and different authoring actions, while the D0 runner permits only source-text XML editing; those are intentional treatment differences. Neither arm in these offline checks executed a model, an untrusted Python program, or an official evaluator.

**More importantly:** the shared toy XML omits the original IFC room's native SpaceType and Pset data. Accordingly:

- `core_source_text_context_equal=true`
- `both_arms_cover_source_native_type_pset=false`
- `model_information_equivalence_proven=false`
- `official_task_eligible=false`

This is not a contradiction: identical partial text inputs can both omit semantically important native IFC information.

The audit never passes hidden GT fields to either runner, and no candidate IFC is persisted except temporarily during the separate manual oracle. The public IFC is byte-for-byte unchanged.

## Regression and failure cases

New tests cover:

- Real pinned input with a source `IfcSpaceType`, two Psets and two original Reference attributes, original metadata preserved and none duplicated in the new Space.
- Denial of an invalid shared Pset or shared SpaceType created by a simulated mutation.
- Denial of an IFC source with an unimplemented geometry-dependent `IfcElementQuantity`.
- Denial of unsupported complex property value forms.
- Real D/I text-observation equivalence and the explicit full-semantic-parity blocker.
- Failure when task instruction, XML projection, XML language spec or source IFC hash differ.

Files:
- `src/runtime/space_metadata_gate.py`
- `src/runtime/space_partition_compiler.py`
- `src/runtime/compiler.py`
- `tests/test_space_metadata_gate.py`
- `tests/test_space_context_parity_gate.py`
- `tools/audit_space_metadata_context_parity.py`
- `tools/verify_declarative_space_pair.py`
- `reports/manual_space_metadata_context_20261110.json`
- `reports/manual_full_declarative_space_pair_metadata_20261110.json`

### Reproduce

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.test_space_metadata_gate tests.test_space_context_parity_gate tests.test_declarative_space_partition_compiler -v
.\.venv\Scripts\python.exe -m tools.audit_space_metadata_context_parity
.\.venv\Scripts\python.exe -m tools.verify_declarative_space_pair
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The two report CLIs return **exit code 2 intentionally**: the limited source-context and deterministic geometry/parity audits pass, but full model-information/fair-evaluation eligibility remains blocked. The original IFC already produces 6 validation errors, while the D0 generated geometry IFC still has 4 inherited errors and **0 new schema-error categories**. No validated claim of a fully schema-clean model is made.

## Scientific limitations and following research gate

To evaluate full task success, future work must define an **explicit, declarative and independently justified source representation** of SpaceType, per-room Psets/Reference, new room number/name and split-aware QTO (including correct rule for creating a new room versus splitting existing identity), rather than copying original values from the native IFC. That representation must be available to both LLM arms under matched information and measured budgets.

Until then, the existing D0/I0 geometry/topology parity remains useful engineering evidence but is **not an official result or proof of semantic BIM equivalence**. The formal benchmark score remains **0 scored tasks**, and no model-provider calls or paid pilot were executed. Frozen 36-case sample, hidden GT separation, eval formulas and production repositories are unchanged.
