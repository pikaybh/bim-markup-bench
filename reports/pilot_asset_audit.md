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

At the initial November 7 audit, **29 pilot tasks** remained unverified. The expanded November 9 check below reduces the outstanding count to **18**.
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

## November 9, 2026: limited incremental public IFC audit

A deterministic fixed-candidate, bounded-download command was added:
tools/cache_small_pilot_ifcs.py. It defaults to a no-network plan and
requires an explicit --apply and --limit-bytes (max 50,000,000 bytes).
Only files referenced by the previously selected 36 task IDs can be
fetched from immutable model revision
0ae510bd21865def4e2c6145c1244f01a1e3bcb9. The tool verifies
the pinned Git blob SHA-1 or LFS SHA-256 and exact file size before
exclusive publication, without overwriting any existing source/GT
bytes. Temporary unverified downloads are removed upon failure.

For this partial audit, the maximum batch allowance was 8,000,000
bytes. The tool actually downloaded **17 files / 4,349,025 bytes**
and validated 11 additional small candidate tasks. Together with
the earlier six pairs, the Windows scratch cache now contains
**29 distinct fixed-pilot IFC assets / 5,907,101 bytes**, supporting
**18/36 tasks** across all six target classes. The other **18/36
candidate tasks** remain without verified input/GT bytes. The entire
36-task candidate references 52 unique files (1,564,261,830 bytes).

These 18 native checks confirm verified file bytes and basic per-target
class/identity/delta consistency only. They do NOT score the
natural-language instruction, full shape/semantic/topology quality,
the official BIM-Edit metric or actual LLM model outputs.
Full 324-task source/GT content and individual model redistribution
rights have not been independently audited.

Reproduce the controlled download on a local machine where trusted
public benchmark metadata and ignored data/ifc scratch are available:

    python -m tools.cache_small_pilot_ifcs --limit-bytes 8000000
    python -m tools.cache_small_pilot_ifcs --limit-bytes 8000000 --apply
    python -m tools.audit_pilot_assets --enforce

The first command is offline planning only. The second explicitly
allows a bounded, hash-verified fetch. The third must exit 2 because
the complete study release gate remains blocked. Never move the GT
scratch into either agent-visible work area.

Windows 11 (Python 3.12.2; IfcOpenShell 0.8.4.post1) full regression
after the limited cache change: **295 tests executed, 283 passed,
12 environment/platform skips, 0 failures**. Linux Docker Desktop
was returned to its original stopped state after the previous
isolated x64 worker verification. The data-audit strict --enforce
gate still returned 2 (BLOCKED), with zero paid calls and zero
official task scores.

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

## November 9 follow-up: 30 of 36 candidate input/GT integrity checks

Following the first bounded 18/36 checkpoint, two further hash-verified
public IFC batches were downloaded to ignored trusted scratch:

- Batch A: 9 unique pinned IFC files, 46,477,832 bytes; 7 additional
  candidate tasks became verifiable (25/36).
- Batch B: 4 unique pinned IFC files, 34,968,195 bytes; 5 additional
  candidate tasks became verifiable (30/36).

Together, the fixed 36-task pilot now has **30/36 verified native
source/GT byte and basic object-class/delta checks**, supported by
**42 unique pilot IFC files totaling 87,353,128 bytes**. Candidate IDs,
G0/G1/G2 readiness flags and the official-scoring gate have not changed.
The latest canonical machine-readable audit is
reports/pilot_asset_audit_partial.json. No agent saw reference content;
all raw IFC files remain local-only, gitignored audit scratch.

The **remaining six tasks** require **10 additional unique source/GT
IFC files totaling 1,476,908,702 bytes**. Minimum per-task incremental
content needs range from 94MB to about 450MB. Even the cheapest
remaining case cannot fit under the tool's safe single-batch cap of
50MB; the dry run returns zero selected tasks. These are NOT marked
passed or audited. Full corpus provenance/individual model rights
still require additional research before large-scale reuse.

**No paid LLM calls and no official scores.** This is not a 30/36
model success rate; it is verified data coverage only. The full 324
source/GT content review and actual experiment remain blocked.

### 30/36 Windows regression evidence

On November 9, the updated frozen audit and additional optional
realistic-pair test ran with the full Windows Python 3.12 suite:
**296 tests executed, 284 passed, 12 skipped, 0 failed**.
The offline audit --enforce correctly exited 2 (BLOCKED).
Docker Desktop was left stopped; skipped Linux-only security cases
are not silently considered passed. Existing independently verified
Linux AMD64 OWN worker findings remain documented in docs/IFC_WORKER.md.
