# G2 #19 — pinned Linux ARM64 Python / IfcOpenShell worker

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
input IFC read-only, an output directory and the trusted test source
read-only. A hidden synthetic GT marker remains outside any mount.

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

- Total writable bind-mount volume quota NOT implemented; 32MiB
  RLIMIT_FSIZE is only PER FILE. Multiple files can still exhaust disk.
- No arbitrary model-code execution interface authorized, no full
  adversarial runtime review, no image CVE/SBOM/signature audit, no
  independent grader kernel sandbox or official GT audit.
- No full 324-task reference IFC data, no verified matched source
  capabilities, no official evaluator parity and no paid-provider
  billing broker. Real model and official scored pilot gates stay BLOCKED.

Xim/BIXML production code, secrets, official task GT and server state
are untouched.
