# G2 #19 — task compartments and measured Docker kernel isolation

**Current state: source/GT file-layout checks PASS; tested Docker kernel
restriction smoke PASS; production Python/IfcOpenShell worker and paid model
trials remain BLOCKED.** Evidence date: November 7, 2026, Asia/Seoul.

## Trusted task file boundaries (earlier #19 partial)

The controller stages separate agent_workspace, trusted_compiler and grader
paths, with deterministic task/arm/seed/source-SHA identifiers. Immutable
input IFC copies have verified hashes. The agent-visible JSON contains only
task instruction, XML model view, language spec, source digest and a basename;
raw task target IDs, hidden GT files, evaluator output and API keys are not
included. Unknown files and symlinks fail staging audit.

These same-user host directories are NOT, by themselves, an OS security
boundary. UNIX 0444 permissions can be overridden by a file owner; the
actual worker must be restricted at the Linux namespace/mount layer.

## Docker Desktop kernel probe executed on this Mac

Docker Desktop 29.4.3 was started and its Linux arm64 engine was reachable.
A fixed own synthetic Python restriction probe ran in a container created
from a locally cached image by exact full SHA256 image ID. The local cached
image comes from another project, so its build provenance has NOT been
audited or scientifically approved as a reproducible worker image.

The harness first creates a stopped container with Docker:
- no implicit image pull; only locally cached exact image sha256 ID
- network=none, root filesystem read-only, all Linux capabilities dropped
- uid/gid 65534:65534, no-new-privileges, default kernel seccomp
- IPC disabled and private cgroups
- memory/swap capped at 128 MiB, 16 PIDs, 0.5 CPU share
- temporary /tmp as a bounded noexec/nosuid/nodev tmpfs
- only TWO bind mounts: own synthetic /input directory read-only and
  own /output directory writable; hidden grader path is NOT mounted
- no Docker socket mounts; no user HOME, ssh-agent or provider key passed
- a deliberately fake parent OPENAI_API_KEY sentinel was set in the
  Docker CLI process only, and absent from the container environment

Before starting the container, Docker inspect must independently confirm
15 host configuration/mount/environment restrictions. Any mismatch REFUSES
START. The fixed trusted probe (NOT model-generated code) then verifies 15
kernel/FS/security properties, including input visible but not writable,
host root write denied, hidden GT path/traversal denied, Docker socket and
parent API secret absent, outbound TCP connection denied, non-root UID,
zero effective capabilities, no-new-privileges=1, seccomp filter active
and cgroup CPU/memory/PID limits. Own input/GT marker SHA values are checked
unchanged after the run; exact namespaced container is removed on exit.

Result: 15/15 prestart + 15/15 in-container checks PASS. No leftover own
probe containers, no generated untrusted Python execution, no provider
calls, no official benchmark output and no paid inference.

## Repeat the local proof without running model code

Use Python 3.12.13 and IfcOpenShell 0.8.4.post1 project environment.
A suitable Ubuntu/Linux image must already be cached locally, must have
/usr/bin/python3 and must be specified by its immutable Docker image ID.
Do NOT pass a mutable tag or unknown image name. Do NOT use another
project's image as the scientifically approved final worker.

    .venv/bin/python -m unittest tests.security.test_docker_isolation -v

To exercise the real daemon, provide BIM_BENCH_DOCKER_PROBE_IMAGE_SHA as
an explicit environment variable containing a cached immutable image ID,
and rerun the test. The trusted CLI can be invoked as:

    .venv/bin/python -m tools.verify_docker_sandbox --image-id sha256:YOUR_FULL_LOCAL_IMAGE_ID
    .venv/bin/python -m tools.verify_docker_sandbox --image-id sha256:YOUR_FULL_LOCAL_IMAGE_ID --enforce-live

The normal CLI outputs kernel evidence only and never starts a provider.
The --enforce-live command MUST return exit code 2 even if all kernel
checks pass; the scientific worker model and paid execution prerequisites
are not satisfied. A recorded sanitized smoke result is available in
reports/docker_kernel_probe_evidence.json. See code for exact OCI options.

## Independent release blockers

- Curated reproducible Python 3.12/IfcOpenShell worker image with source,
  digest, dependency SBOM/signature/licensing and provider patch levels.
- A dedicated worker process restricted to exact source IFC and empty output
  directory. The present trusted fixed probe is NOT a generic untrusted
  generated-Python executor.
- Real worker resource and output quotas including stdout/stderr/disk limits,
  process-level timeout cleanup, and validation of malicious Python probes
  inside the *curated worker* (not inside a shared unrestricted host).
- Verified command/tool isolation, file path traversal and prompt-injection
  defenses for true generated source, not merely the frozen probe script.
- Private GT/official IFC corpus byte audit, scorer provenance and paired
  observation/capability parity; exact model/prices and durable paid billing
  broker with explicit user authorization.

**Thus Issue #19 cannot close, the G2 live/pilot release gate stays
BLOCKED, and src/runner/sandbox.py continues to refuse generated Python.**
Do not treat a passing smoke or an available Docker socket as permission
to execute untrusted model output.
