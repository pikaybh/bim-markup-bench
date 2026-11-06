# BIM-Edit pinned metadata integrity audit — G0 Issue #3

**STATUS: PARTIALLY VERIFIED — ISSUE OPEN.** This is NOT an audit of downloaded IFC bytes, real source/GT geometry or scorer behavior.

## Pinned sources

- Task dataset: https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks/tree/2dc6462bfab145ddf81b43e9954322855b8443dc
- IFC model dataset: https://huggingface.co/datasets/BIM-Edit/BIM-Edit/tree/0ae510bd21865def4e2c6145c1244f01a1e3bcb9
- Public task JSONL SHA-256: 9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83
- Model repo card advertises CC BY 4.0; individual model rights and redistribution remain unverified.

## Findings

| Check | Actual observation |
| --- | --- |
| Tasks and distinct IDs | 324 / 324 |
| create / update / delete | 108 / 108 / 108 |
| direct / spatial / topological | 108 / 108 / 108 |
| synthetic A / realistic R | 162 / 162 |
| IFC classes | Wall/Slab/Space 72 each, Door/Window/Column 36 each |
| 18 operation × category × scene strata | Exactly 18 tasks each |
| Target GUID metadata | Compressed 22-character syntax valid; create zero, edit/delete one |
| Unique referenced IFC paths | 148 |
| Referenced paths found in pinned remote file tree | 148 / 148 |
| Total IFC objects in remote tree | 151 (three unreferenced) |
| Remote repository file bytes | 4,310,158,877 |
| Remote IFC with LFS SHA-256 pointers | 33 |
| Remote IFC with only Git blob OIDs | 118 |
| Actual IFC content downloaded and independently hashed | **NOT DONE** |
| Source→GT elements, GUIDs and IFC geometry/relationship deltas | **NOT DONE** |

### Important folder alias correction

The task JSONL uses data/realistic/ and data/artificial/, but the model repository uses complex/ and simple/ respectively. The 148 referenced asset paths match **exactly** using realistic → complex and artificial → simple. The reverse mapping matches 0/148. No upstream task file was modified.

The pinned model revision includes an upstream rename repairing a complex filename with repeated .ifc.ifc extension (August 17, 2026); this cannot establish the absence of content-level GUID issues.

### Code and safety

- src/data/bim_edit.py: SHA check, raw metadata field and GUID validation, six-class and 18-stratum checks, strict alias mapping, remote tree count comparison.
- schemas/task_manifest.schema.json: schema of GRADER-only task rows; never send raw task metadata to LLM.
- agent_view: strips target, evaluation and GT paths; only task ID, natural-language instruction and input.ifc sandbox alias are passed onward.
- tools/audit_bim_edit.py: downloads only small public JSONL and repository metadata via a pinned revision, **never the 4.31GB IFC corpus**.
- .gitignore fixed to ignore only root data/ so src/data/ source is trackable.

## Reproduction

1. uv sync --frozen --python 3.12
2. .venv/bin/python -m tools.audit_bim_edit --fetch-metadata-only
3. .venv/bin/python -m unittest discover -s tests -v

Raw remote records remain in gitignored data/. The version manifest in manifests/ explicitly reports content_verified = false and gate_passed = false.

## Blockers required to close Issue #3

1. Explicit storage/usage authorization for ~4.31GB source and GT IFC corpus and file provenance check; no unapproved bulk download.
2. Actual local SHA-256 or Git blob digest recomputation of all 148 referenced files; remote pointers alone are **not** verified bytes.
3. Parse each IFC with pinned IfcOpenShell and inspect target GUID class, source vs GT edit deltas, host/space topology. Report mismatches without silently repairing dataset.
4. Validate per-file redistribution permissions and keep grader-only GT outside model and agent sandbox.

## One real input IFC verified (small, non-bulk smoke)

Downloaded **only** the 15,313-byte file simple/17_input.ifc from the pinned 0ae510bd model revision into ignored local data/ifc. Its byte content matched the remote Git blob SHA-1 pointer, and the pinned IfcOpenShell 0.8.4.post1 opened it successfully. Observed schema: **IFC4X3**, one IfcProject and five IfcWall entities. This is **one-file positive evidence only**. The synthetic environment doctor used IFC4; neither proves that all BIM-Edit assets have a uniform schema.
