# G2 #19 - pinned Linux ARM64/AMD64 Python / IfcOpenShell worker

**Status:** purpose-built isolated worker executed OWN synthetic IFC tests,
but arbitrary LLM-generated Python and paid pilots are STILL BLOCKED.

## Build and dependency provenance

- Base: official Python 3.12.16 Linux ARM64 slim-bookworm,
  pinned manifest sha256:df540bfd30bd380e89a349611ce42aa67bcb542d58c047706616eb6ba2f86a1b
- Python package: ifcopenshell==0.8.4.post1
- All transitive wheels pinned with versions and hashes in
  docker/ifc_worker/requirements.lock. Hash checking and binary wheels only.
- No model provider SDK or dotenv in the worker image.
- Build command from repository root:

    docker build --platform linux/arm64 --pull=false -f docker/ifc_worker/Dockerfile -t bim-markup-bench/ifc-worker:0.1.0 .
    docker image inspect bim-markup-bench/ifc-worker:0.1.0 --format '{{.Id}}'

A new local immutable image ID is produced by the build. Dependency and
base pinning does not itself prove byte-for-byte identical final OCI images
across different build machines. No signed SBOM/CVE review is available yet.

## Actual tested restricted execution

The runner src/runner/ifc_worker.py executes exactly five OWN constant
fixture programs; arbitrary model code cannot be submitted to it.

For each trial it verifies the cached immutable Docker image ID and
labels, builds a new isolated task directory, verifies the container
configuration BEFORE starting the container, mounts only the own small
input IFC and trusted test source read-only. The writable /output
is a 64MiB bounded tmpfs inside Linux, never an unbounded Windows
host-directory bind. A hidden synthetic GT marker remains outside all mounts.
Only an OWN fixture IFC no larger than 256KiB may be returned as checked
base64 through the trusted wrapper; official models are not exported.

Flags: network=none, root filesystem read-only, UID/GID 65534,
capabilities all dropped, no-new-privileges, PID limit 1, RAM/swap
512MiB, 0.75 CPU, private cgroup, no IPC, bounded noexec tmpfs.
The controller strips parent secrets, uses no model API and force-removes
only its own namespaced container after execution.

OpenBLAS thread count is fixed to 1 because its default multi-threaded
initialization failed under the PID limit of 1. The native worker
successfully imported Python 3.12.16/IfcOpenShell 0.8.4.post1, read,
meshed, wrote and reopened an IFC4X3. Another fixed program edited
the Wall extrusion depth from 3.0 to 3.3m.

The negative fixture verified input write, GT path, traversal, Docker
socket, parent API key, external TCP, rootfs write and subprocess spawn
denials. A 33MiB write exceeded the 32MiB per-file hard limit;
five attempted 24MiB files hit the 64MiB whole-directory tmpfs cap;
an intentional infinite loop was killed by the external 3s cutoff.
All original input and GT marker bytes remained unchanged and
all created containers were removed.

## Local reproduction

    export BIM_BENCH_IFC_WORKER_IMAGE_SHA="$(docker image inspect bim-markup-bench/ifc-worker:0.1.0 --format '{{.Id}}')"
    .venv/bin/python -m unittest tests.security.test_ifc_worker -v
    .venv/bin/python -m tools.verify_ifc_worker --image-id "$BIM_BENCH_IFC_WORKER_IMAGE_SHA"
    .venv/bin/python -m tools.verify_ifc_worker --image-id "$BIM_BENCH_IFC_WORKER_IMAGE_SHA" --enforce-live

The final command must exit with code 2 and say BLOCKED, even if
every OWN synthetic OS security test passes. Evidence with no host
image ID or secrets is in reports/ifc_worker_smoke_evidence.json.

## Outstanding blockers

- The own-fixture worker has a 64MiB whole-directory tmpfs quota
  and 32MiB per-file limit; however production-grade result exporting,
  robust hostile-code fuzzing and an independently reviewed untrusted
  task submission API are NOT implemented.
- No arbitrary model-code execution interface authorized, no full
  adversarial runtime review, no image CVE/SBOM/signature audit, no
  independent grader kernel sandbox or official GT audit.
- No full 324-task reference IFC data, no verified matched source
  capabilities, no official evaluator parity and no paid-provider
  billing broker. Real model and official scored pilot gates stay BLOCKED.

Xim/BIXML production code, secrets, official task GT and server state
are untouched.

## Windows 11 Linux AMD64 execution (2026-11-09)

The original ARM64 image is not usable natively on this x64 PC.
A separate amd64 image was built from the official Python 3.12.16
manifest sha256:0f086103b026048cc50cb5da25ec435c023c5241a83fc44daea593377abc61c4
and requirements.amd64.lock, generated from the same direct pins for
Linux x86_64 with hashed binary wheels. It is intentionally a separate,
immutable platform-specific image; Docker tags are never accepted as
execution image identifiers.

Windows project root:
D:\문서\D__1_Projects\202611\bim-markup-bench.
Docker Desktop Linux backend 28.3.2, WSL 3.0.3 on Windows 11,
architecture x86_64/amd64. WSL was already present; no OS feature
installation or restart was needed.

PowerShell from project root:

    docker build --platform linux/amd64 --pull=false -f docker/ifc_worker/Dockerfile.amd64 -t bim-markup-bench/ifc-worker:amd64-0.1.0 .
    $env:BIM_BENCH_IFC_WORKER_IMAGE_SHA=(docker image inspect bim-markup-bench/ifc-worker:amd64-0.1.0 --format '{{.Id}}').Trim()
    .\.venv\Scripts\python.exe -m unittest tests.security.test_ifc_worker -v
    .\.venv\Scripts\python.exe -m tools.verify_ifc_worker --image-id $env:BIM_BENCH_IFC_WORKER_IMAGE_SHA --enforce-live

The verify command must return 2 in enforced mode and never authorizes
live model-generated programs or a paid research run. The actual
Windows native IFC, file/GT/network/process denials, 32MiB file limit,
64MiB total-output tmpfs quota and 3-second infinite loop cutoff
were tested using only owned synthetic programs. The controller
inspects Docker HostConfig before starting every container and
removes only its namespaced containers afterward.

reports/ifc_worker_windows_amd64_evidence.json records the sanitized
pass/block result. No user API key, official reference IFC data, or
private model file was used. The scientific release gate remains
BLOCKED until the model-code interface, independent grader isolation,
scorer parity, full corpus and billing controls are verified.


## Offline dynamic Python + independent OWN Linux grader (partial #19)

The separate src/runner/generated_candidate.py path accepts SHA256-pinned
arbitrary Python program bytes, but ONLY with repository-created synthetic
input.ifc. It never imports or executes those bytes on the host.
A read-only candidate container returns at most one 256KiB IFC with
bounded stdout/stderr/overall tmpfs quotas. The candidate container is
removed before a SEPARATE Linux Docker grader is allowed to receive the
trusted OWN synthetic GT file. The grader does not see the candidate
Python script, uses three strictly read-only mounts, and checks its own
HostConfig before running. A host process independently verifies native
STEP integrity as well. This demonstrates compartment separation
ONLY for the owned fixture; it does NOT validate the full official
independent BIM-Edit scorer or enable paid model-generated runs.

Run with an exact immutable image ID:

    .\.venv\Scripts\python.exe -m unittest tests.security.test_generated_candidate -v
    .\.venv\Scripts\python.exe -m tools.verify_dynamic_candidate --image-id sha256:EXACT_CACHED_NATIVE_WORKER_ID --enforce-live

The enforced verification must exit 2 (BLOCKED). See
reports/dynamic_own_candidate_evidence.json and
docs/SECURITY_ISOLATION.md for exact limitations and negative cases.
