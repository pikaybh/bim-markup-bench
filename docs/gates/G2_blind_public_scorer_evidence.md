# G2 #21 — Pinned public IFC blind-scoring compartment (partial)

**Gate: BLOCKED_FOR_LIVE_MODEL_PILOT.** This document records a trusted
evaluator self-check, NOT an official BIM-Edit result or LLM experiment.

## Immutable inputs and scope (2026-11-09)

- Windows root: `D:\문서\D__1_Projects\202611\bim-markup-bench`
- Linux x64 Docker Desktop engine 28.3.2, Python 3.12.16,
  IfcOpenShell 0.8.4.post1.
- Grader image (local immutable ID):
  `sha256:fb16105fe69bb87f0ab15390a14733e2c734f0f13e774b1767c57f5b296dbf8d`
- Base image: official Linux amd64 Python slim-bookworm manifest
  `sha256:0f086103b026048cc50cb5da25ec435c023c5241a83fc44daea593377abc61c4`
- Pinned Linux amd64 dependencies:
  `docker/ifc_worker/requirements.amd64.lock`, all wheel hashes required.
- Public source/GT dataset immutable model revision:
  `0ae510bd21865def4e2c6145c1244f01a1e3bcb9`.
  The existing fixed 36 pilot IDs were not changed.
- Three already-audited, small public tasks: `WAL-UPD-TOP-A-001`,
  `WAL-DEL-TOP-A-001`, `DOR-CRE-TOP-A-002`.
  Both source and reference bytes are verified against pinned Git/LFS
  remote object metadata before grading. These public IFCs stay local
  and untracked; no GT or target GUID is committed to Git.
- Metric origin: **`independent-reimplementation`**,
  evaluator version `independent-ifc-three-axis-v0.1`.
  **Official evaluator equivalence: false.**

## Architecture and independent score boundary

The independent grader code is **baked into a dedicated image**, separate
from the candidate worker, with only evaluator Python modules included.
An allowlist-only `.dockerignore` excludes the entire local IFC cache,
raw GT data, .env/credentials, Git history, generated experiments and
unrelated source code from the Docker build context.

The actual Docker grader namespace receives exactly **four read-only
mounts**, each staged in a fresh temp directory by the trusted host
controller: source IFC, hidden GT IFC, candidate IFC and a minimal
grader-only target metadata JSON. Candidate Python, direct XML source,
agent workspaces, compiler code and experiment-arm labels are **not
mounted**. The grader has no network, a read-only root, non-root UID
65534, no added Linux capabilities, no-new-privileges, 1 PID, 512MiB
memory/swap, 0.75 CPU and a 16MiB noexec/nosuid/nodev tmpfs. No host
writable output volume. Docker HostConfig is checked BEFORE container
start; unexpected mounts, writable GT, injected env secrets or arm labels,
changed entrypoint, altered command, network access and privilege changes
are rejected. Runtime stdout/stderr is bounded by the trusted host
controller. All containers are forcibly removed by owned unique name.

Scorer output exposes only whitelisted axis scores, strict pass,
version/provenance and failure status. The host rejects extra keys
including GT paths/hashes, target GUIDs or source code. The source,
reference and candidate files are rehashed after scoring. This path
runs no model-provided Python and no provider API; only three frozen
reference/control conditions are permitted.

## Observed Linux AMD64 results

1. Reference self-check: each of three public tasks scored Geometry,
   Semantics and Topology = **1.0** against itself, strict pass true.
2. An unchanged source on the wall-update task: strict pass **false**
   with actual independent native geometry and topology reductions.
3. Non-IFC candidate bytes: **INVALID_OUTPUT_IFC**, all axes **0.0**.
4. Repeated identical source/condition: same deterministic run ID and
   independent result. No own grader containers remained.
5. **Nine** isolated-grader tests passed, including ten prestart
   HostConfig/sensitive-data negative variations and malformed output
   contracts. Full regression numbers are recorded separately below.
6. Model calls **0**, official benchmark tasks scored **0**.
   This verifies scorer behavior, not a model task-success rate.

Machine-readable sanitized evidence:
`reports/isolated_blind_public_scorer_evidence.json`.

## Reproduce without making paid calls

From the Windows project root, with Docker Desktop Linux engine running:

```powershell
docker build --platform linux/amd64 --pull=false -f docker/ifc_blind_grader/Dockerfile.amd64 -t bim-markup-bench/blind-scorer:amd64-v0.1 .
$env:BIM_BENCH_BLIND_SCORER_SHA256=(docker image inspect bim-markup-bench/blind-scorer:amd64-v0.1 --format '{{.Id}}').Trim()
.\.venv\Scripts\python.exe -m unittest tests.security.test_blind_public_ifc_grader -v
.\.venv\Scripts\python.exe -m tools.verify_blind_public_scorer --image-id $env:BIM_BENCH_BLIND_SCORER_SHA256 --enforce-live
```

The enforced verification **must exit 2** even if all independent
self-checks pass. The main paid-pilot preflight must also exit 2.
The local image tag is a build convenience; every execution uses the
exact immutable SHA256 image ID. If source code or dependencies change,
rebuild and re-verify before changing the recorded ID.

## What this does not establish

This is **not** a complete official BIM-Edit scorer, a real-world
generated-candidate run, a calibration against an available official
implementation, a complete model/task/GUID rights review, or proof
that XML and Python arms have matched capabilities. The full public
324-task IFC content audit, 6 remaining 36-pilot IFC cases, scorer
provenance comparison, budget broker and explicit paid-call approval
are all incomplete. Issue #21 and G2 remain OPEN/BLOCKED. Never turn
reference-vs-reference self-checks into official benchmark success claims.

## Final Windows QA snapshot, 2026-11-09

Full test command (actual cached Linux amd64 native worker and blind
scorer image IDs provided as environment variables):

    .\.venv\Scripts\python.exe -m unittest discover -s tests -v

**316 tests executed, 309 passed, 7 platform/dependency skips,
0 failed (181.838 seconds)**. The primary pilot preflight exited **2**
(BLOCKED), with no paid provider calls. Existing 30/36 native source/GT
byte-audit coverage was preserved without extending the candidate set.
All run-specific blind/OWN candidate/grader containers were removed.
The generated evidence contains no target GUID, hidden reference path
or program source. The independent baseline reference comparisons are
NOT genuine scored model submissions and cannot be counted as a model
success rate or as official BIM-Edit scoring.
