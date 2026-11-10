# G2 #19 — local Python worker admission preflight (Windows 11, 2026-11-10)

**Status: BLOCKED_LOCAL_DOCKER_ENGINE_UNAVAILABLE.** The repository's
existing OWN-synthetic dynamic-Python worker has a historically demonstrated
Docker Linux isolation proof from 2026-11-09; the **current connected Windows
11 Docker Linux daemon is unavailable**. That difference matters: the past
positive report is evidence of an earlier OWN-only demonstration, **not**
evidence that arbitrary model-generated BIM-Edit code may execute now.

## Real observed host status

- `docker.exe` is installed under Docker Desktop, but
  `docker info --format '{{.ServerVersion}}'` fails to reach
  `//./pipe/dockerDesktopLinuxEngine`.
- `com.docker.service` is **Stopped** (Manual start).
- Existing WSL distributions are present, but **no WSL distribution, Docker
  Desktop service, image build, container or other host service was started**.
- The historical OWN-only image is pinned as
  `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`.
  Its **current local cache status, actual image build provenance and
  kernel isolation have NOT been verified**. A source file SHA or historical
  image-id record is not a supply-chain attestation.

## Actual implementation

`src/runner/worker_admission.py` provides an **opaque code admission
contract** and a **read-only** local Docker/image evidence checker. It cannot
run a candidate or approve external IFC/LLM evaluation.

- `bind_own_candidate` accepts exactly the immutable repository-owned
  tiny synthetic IFC and `imperative_python` arm; it verifies source SHA,
  separately supplied candidate SHA and opaque UTF-8 <=64KiB source bytes.
  No agent IFC path, target, scorer, dataset record, provider credentials
  or arbitrary command can be supplied. Unique replay/run IDs bind source,
  script bytes and seed; changing code while keeping the same seed must
  change run ID.
- This strict source/code admission is also enforced **inside the existing
  `run_offline_own_generated_candidate` function before Docker image
  lookup or any possible container activity**. The original G2 production
  `src.runner.sandbox.execute_untrusted_candidate` remains an unconditional
  hard denial. This integration does not promote the OWN-only path.
- The local Docker probe forces a platform-owned local socket, not a
  caller-selected Docker context or `DOCKER_HOST`. It executes only
  `docker info` and, if the daemon is reachable and Linux-native,
  `docker image inspect sha256:...`. It never invokes `start`, `run`,
  `create`, `pull`, `exec`, `wsl`, a service manager, or Python source.
  It rejects remote host environment selectors, malformed/oversized
  inspect responses, non-Linux architectures, absent cached image, wrong
  native architecture, wrong image digest, root default user and missing
  worker label.
- Even if the local Docker daemon and pinned image are both verified,
  the highest attainable status is
  `READY_FOR_TRUSTED_OWN_PROBE_ONLY_NOT_GENERATED_PYTHON`.
  This explicitly **does not** assert current OS kernel isolation,
  proven image SBOM/build provenance, official scorer, live Python tool
  readiness, full external model support or paid-model approval.

Structured evidence `reports/local_worker_admission_20261110.json` contains
only source/code/worker image digests, status flags and counts. It includes
no Python source, IFC data, task instructions, hidden GT, scores or secrets.

## Test evidence

`tests/security/test_worker_admission.py` tests source/code hashes, direct
arm rejection, replay ID isolation, invalid seed/script data, mutable image
tags, daemon offline and missing cached image, hostile/non-Linux platform,
forged image digest/user/label, malformed Docker JSON, explicit local socket
and secret sanitization, and the existing OWN worker's early-admission path.

A mocked positive image inspection is **only** a proof of control-flow and
cannot substitute for an actual Docker kernel test. The actual Windows probe
also returns blocked, with no service or process mutation.

### Reproduce

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.security.test_worker_admission -v
.\.venv\Scripts\python.exe -m tools.audit_local_worker_admission
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The read-only evidence tool intentionally returns **exit code 2** while
current local Docker admission and the downstream G2/G3 model/scorer budgets
remain blocked.

## Remaining security and scientific barriers

A production-grade isolated I0 worker still needs: available **local**
Docker Linux daemon; exact cached image/SBOM/build attestation; a fresh
kernel/mount/network/capability test with the actual intended worker;
independently reviewed separate source/code/result/GT and evaluator
compartments for every new external BIM-Edit task; output/log/resource
limits on arbitrary Python; real provider budget owner approval and exact
model token accounting. The recorded OWN-only dynamic adversarial smoke
is valuable but **not** proof of general arbitrary code safety.

The actual Docker code-path controls must also remain bound to the same
local endpoint as their admission check before any broader worker
approval. A read-only check against the local pipe alone cannot attest
an execution subsequently sent through a caller-mutable different Docker
context.

Do not infer official benchmark correctness. Official tasks scored **0**;
paid/provider model calls **0**; G2/G3 live pilot **BLOCKED**.
