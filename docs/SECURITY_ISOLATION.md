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


## 2026-11-09 — Dynamic Python candidate on OWN IFC, Linux AMD64 (partial)

The previously fixed-only worker has a separate controlled offline synthetic
route: src/runner/generated_candidate.py. It accepts opaque UTF-8 Python
program bytes from a trusted caller, checks a separately provided SHA-256,
and NEVER imports/evals/executes candidate code on the Windows/Mac host.
Source data are pinned internally to the own small synthetic
tests/fixtures/synthetic/input.ifc. No external IFC path is allowed.

The immutable Linux worker image must match the Docker daemon's native
architecture. Each attempt creates a new namespaced container with only
two read-only bind mounts: /input/input.ifc and /task/solution.py. The
/output and /tmp locations are capped at 64MiB/16MiB tmpfs and there is no
GT/grader or shared host output mount. HostConfig is checked BEFORE start.
Guest execution uses no network, capabilities dropped, uid 65534, readonly
root, no-new-privileges, default seccomp, PIDs=1, memory=512MiB,
CPU=0.75, per-file size=32MiB, stdout cap=512KiB, stderr cap=16KiB,
and external timeouts <=20s. Docker CLI runs with a minimal host
environment and no inherited provider keys.

Only one <=256KiB OWN IFC is allowed back. The host checks file encoding
and size, source/script/hidden OWN-GT canary hashes and explicitly
removes the candidate container BEFORE invoking the grader. Two OWN
verification paths then run without importing candidate code:
(1) a trusted host process in src/runner/own_result_grader.py and
(2) a SEPARATE Linux container in src/runner/own_grader_container.py.
The second container has three read-only mounts: own source,
returned candidate IFC and OWN synthetic expected GT. Its HostConfig
is independently checked before start: no /task, no executable candidate
script, no shared writable mount, no network or provider credentials.
The candidate container never sees the expected GT mount. The narrow
oracle requires IFC4X3, exactly one Wall, unmodified root IDs/classes,
height 3.0 to 3.3m and exactly one changed IfcExtrudedAreaSolid STEP
instance. The independent Linux grader also verifies the OWN reference
height 3.3m. This is an OWN-only regression oracle, NOT the official
BIM-Edit scorer.

Actual observed Windows 11 Linux x64 cases: arbitrary owned Python
program absent from the worker's fixed list changed its synthetic IFC;
the separate trusted host grader validated it. A different owned
dynamically supplied adversarial program first attempted original IFC
write, GT path read, secret env access, outbound socket and subprocess
and found each denied before performing the same valid IFC edit.
Same code + seed + source gives identical run ID and result SHA.
Missing output, duplicate/forged result, unrelated IFC mutation, bad
candidate hash and stdout flooding were rejected. Grader tests
separately prove that a script mounted into the grader, writable GT,
missing GT, inherited API key or changed grader command is rejected
BEFORE starting. A wrong synthetic GT is rejected during actual Linux
native grader execution. Both own Docker namespaces are cleaned.

Reproduce on the confirmed Windows project path with Docker Desktop
running and the cached exact image:

    $env:BIM_BENCH_IFC_WORKER_IMAGE_SHA=(docker image inspect bim-markup-bench/ifc-worker:amd64-0.1.0 --format '{{.Id}}').Trim()
    .\.venv\Scripts\python.exe -m unittest tests.security.test_generated_candidate -v
    .\.venv\Scripts\python.exe -m tools.verify_dynamic_candidate --image-id $env:BIM_BENCH_IFC_WORKER_IMAGE_SHA --enforce-live

The enforced command must return code 2. A sanitized owned-proof artifact
is recorded at reports/dynamic_own_candidate_evidence.json.

NOT production-ready: the real src.runner.sandbox.execute_untrusted_candidate
entrypoint still unconditionally refuses dynamic execution. External BIM-Edit
IFC/tasks, actual provider-produced Python, independently validated
OFFICIAL scorer parity, complete worker/grader image provenance/SBOM/fuzzing,
cost broker and paid pilot remain unverified or disabled. An independent
Linux grader container has been shown only for OWN synthetic reference
data, with the same pinned scientific worker image, NOT the external
official GT/scoring engine; do not infer real dataset GT safety from the
own fixture proof. A security and methodology review is required before
expanding this entrypoint.

### November 9 Windows full regression and release-gate record

The completed Windows 11 Python 3.12 + Docker Linux AMD64 suite
executed **306 tests; 299 passed, 7 platform/dependency skips, 0
failures**. This includes the dynamic candidate in its own Linux
namespace, the independent OWN-reference grader container, denied
file/network/process/secret probes, stdout flood, wrong GT,
HostConfig manipulation, deterministic replay and native STEP diff.
Both the primary pilot preflight and dynamic OWN --enforce-live checks
returned exit code **2 (BLOCKED)**. No real provider, paid model,
external benchmark GT or official scorer run occurred.

The experimental image was the locally cached exact native Linux
AMD64 ID sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee.
Source IFC SHA-256: 10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.
The test host did not modify production Xim/BIXML or other projects.
