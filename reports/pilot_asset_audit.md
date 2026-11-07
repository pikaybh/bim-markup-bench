# BIM-Edit 36-case candidate — partial actual IFC byte audit

**Date:** 2026-11-07 · G0 #3 status: PARTIAL / full 324 IFC content
gate remains BLOCKED. **No official IFC edit task has been scored.**

Data pinned:
- Public 324-task JSONL: task revision
  2dc6462bfab145ddf81b43e9954322855b8443dc
- IFC model revision: 0ae510bd21865def4e2c6145c1244f01a1e3bcb9
- Existing task JSONL SHA-256:
  9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83
- Public candidate: manifests/pilot_36_candidate_v0.json

## Scope and actual observations

The 36 previously selected fixed task IDs refer to **52 distinct
input/GT IFC assets**, with 1,564,261,830 bytes total according to
pinned remote file size metadata (~1.56 GB decimal). The entire
model repo has 4,310,158,877 bytes of remote files, and the full 324
task population references 148 distinct IFC assets.

**Six small source/GT pairs (12 unique IFC files, 1,558,076 bytes)**
were downloaded into ignored scratch. They cover seven fixed task IDs
across all six IFC target classes, because two Space tasks share one
source/GT pair. This is a data audit only; the 36 candidate IDs were
not altered.

The smallest Wall example is WAL-CRE-SPA-A-003 (223,015 bytes):
- Original source 110,571 bytes, verified against original Git blob SHA-1
- Reference GT 112,444 bytes, verified against original Git blob SHA-1
- Both files independently read as actual IFC4X3 by the pinned
  IfcOpenShell 0.8.4.post1 parser
- The original contained four IfcWall products; its GT contained five
  and exactly one new IfcWall GlobalId, consistent with the task being
  a create operation
- Original data were not edited and the IFC binary contents are NOT
  tracked in the Git repository

The remaining **29 pilot tasks** have NOT been byte-verified.
Verified operation/classes: IfcWall CREATE, IfcSlab CREATE,
IfcWindow CREATE, IfcDoor DELETE, IfcColumn DELETE, and
IfcSpace UPDATE (two tasks sharing one pair). All six types
passed the basic integrity and native class/change check. No
claim is made about full semantics, topology or instruction quality.
The machine-readable report is reports/pilot_asset_audit_partial.json;
it contains only task IDs, operation/class, byte sizes, boolean
checks, scrubbed status codes and aggregate counts. It deliberately
does not include GT paths, target GUIDs, natural-language task prompts
or any IFC file bytes.

## Auditor behavior and trust boundary

The offline tool tools/audit_pilot_assets.py accepts the fixed 36-task
candidate, verified pinned metadata and a local scratch root. It
requires remote paths and sizes to match a known fixed revision,
disallows symlink/traversal, and verifies every available file against
either the remote LFS SHA-256 digest or Git blob SHA-1 digest. Only when
both input and GT are present and verified does the **trusted audit
process**, not the agent, load IFC and inspect native target-class
deltas. Create requires exactly one newly added class product; delete
requires removal of the existing target GUID; update requires target
GUID retention and an observable product property/pose/mesh signature
change. These checks are intentionally narrower than a full official
task quality score and may miss more subtle IFC relationships.

Malformed IFC or changed original/GT bytes, missing assets, target
class mismatch, symlink escape and no-op updates yield explicit
blocked results. The auditor is not imported by any direct XML/agent
interface and does not access provider keys.

## Reproduction, no network IFC downloads

    .venv/bin/python -m tools.audit_bim_edit --fetch-metadata-only
    .venv/bin/python -m tools.audit_pilot_assets \
       --asset-root data/ifc --output-json /tmp/new-pilot-audit.json
    .venv/bin/python -m unittest tests.test_pilot_asset_audit -v

The audit command is **offline**. It never auto-downloads IFC assets;
input files must already be present in the trusted ignored local cache.
The --enforce switch returns code 2 until the full 324 IFC byte audit
and other protocol gates have passed.

## Blockers and caveats

- The current disk has limited free space and the pilot is 1.56 GB
  of unique IFC assets; a complete download requires an explicit
  storage and rights review. No bulk downloads were made.
- Dataset card metadata advertises CC BY 4.0, but individual model
  origin and redistribution rights are NOT independently verified.
- Even for the six verified source/GT pairs, full geometric/
  semantic/topological correctness of each instruction and official
  evaluator success have NOT been established; only integrity and
  basic native class/change observations.
- 324/324 full source/GT IFC content and exact target integrity checks
  remain outstanding. G2/G3 gates and paid experiments remain blocked.
- No production Xim/BIXML, proprietary files or API keys were touched.
