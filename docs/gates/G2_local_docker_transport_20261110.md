# G2 #19 — binding ALL OWN Docker commands to one local daemon

**2026-11-10 · Research gate remains BLOCKED for model-generated Python /
external BIM-Edit scoring.**

## Finding and correction

PR #78 verified a **read-only** local Docker admission check, but the
existing own-synthetic worker paths in `ifc_worker._run`,
`generated_candidate._limited_attach` and the trusted
`docker_isolation._invoke` still allowed the Docker CLI to choose the
host's **implicit Docker context**. An operator's `DOCKER_CONTEXT`,
`DOCKER_HOST`, `~/.docker/config.json` default context or other
custom client configuration could therefore change which daemon executes
`create`, `start`, `attach`, `inspect` or `rm`. A local-only
preflight is not sufficient if subsequent code uses a different daemon.

This PR adds `src/runner/local_docker_transport.py` as the **single
fixed-daemon endpoint source**. The read-only admission checker imports
the same endpoint function; OWN worker, OWN independent grader,
OWN dynamically submitted opaque Python program, Docker kernel probe,
and the Docker attached-output reader all pin `--host` directly
after the Docker executable, for **every invocation**, including cleanup.

The trusted local endpoint is explicitly:

- Windows Docker Desktop **Linux Engine**:
  `npipe:////./pipe/dockerDesktopLinuxEngine`
- macOS Docker Desktop: the current user's
  `~/.docker/run/docker.sock`, only if an existing real, non-symlinked
  Unix socket.
- Native Linux: `/var/run/docker.sock`, only if an existing real,
  non-symlinked Unix socket.

No remote TCP/SSH daemon, mutable Docker context, Docker TLS mode or
symlinked socket is accepted as a fallback. Calls including
`-H`, `--host`, `--context`, `--config`, `--tls`,
`--tlsverify`, `--tlscacert`, `--tlscert` or `--tlskey`
as competing CLI arguments fail before subprocess dispatch.

The existing `_host_docker_env` sends a minimal host environment and
does not inherit `DOCKER_HOST`, `DOCKER_CONTEXT`, registry
credentials, cloud provider keys or private SSH agents. The trusted
kernel probe deliberately sets a **fake** API-key sentinel in the
Docker control process only; its existing container HostConfig and
kernel verification require that sentinel to be absent from the
container. All tests are synthetic and the original source-visibility,
no-network, read-only mount and resource restrictions remain unchanged.

The present helper is a routing boundary, **not** an approval of arbitrary
Python execution, a verified local daemon, a signed image SBOM, or a
universal Docker escape prevention mechanism.

## What was actually tested

`tests/security/test_local_docker_transport.py` verifies:

- One fixed local endpoint even when the *test controller* environment
  contains a fake malicious `DOCKER_HOST=tcp://...` and a remote context.
- All seven representative OWN CLI operations: image inspect, create,
  container inspect, start, delete, `ps`, and daemon info. Full actual
  execution uses the same common `_run` routing helper.
- Candidate attached-output `Popen` uses that endpoint, not a bypass
  through the ambient Docker context.
- Trusted OS isolation probe's separate `subprocess.run` uses that
  same endpoint and an isolated environment.
- Rejection of competing `--host`, `-H`, `--context`,
  `--config` and TLS selectors, accidental arbitrary executable
  invocation, invalid CLI arguments, unsupported platforms, missing
  or symlinked Unix sockets, and untrusted-control execution attempts.
- Historical OWN admissibility, independent grader and worker security
  tests still pass in the offline suite.

This is an **offline mocked CLI argument audit**: it does not execute a
real Docker container or prove live Linux kernel isolation. The separate
read-only `tools.audit_local_docker_transport` checks mocked call
routing while independently performing the currently permitted
`docker info` / `image inspect` **read-only** local admission step.
All four operational code paths are covered; the summary records
only invocation counts/status and intentionally exits **2**.

Sanitized report:
`reports/local_docker_transport_20261110.json`

On the connected Windows 11 PC, the local Docker Desktop Linux Engine
pipe is still unavailable. Thus:

- All mocked CLI controls use
  `npipe:////./pipe/dockerDesktopLinuxEngine`.
- Real Docker daemon reachable: **No**.
- Cached pinned image and current kernel isolation: **Unknown/Unverified**.
- Real candidate Python/container executions this turn: **0**.
- Official BIM-Edit benchmark scores: **0**.
- LLM/provider calls, actual billable tokens and USD: **0 / unknown usage**.
- The `src.runner.sandbox.execute_untrusted_candidate` production
  entrypoint still rejects generated Python unconditionally.

## Reproduce

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest tests.security.test_local_docker_transport -v
.\.venv\Scripts\python.exe -m tools.audit_local_docker_transport # expected exit 2
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

No services, host containers, network image downloads, hidden GT IFC,
third-party Xim/BIXML repositories or external provider credentials are
modified. The pre-registered 36-task set and G2 model-visible inputs are
also unchanged.

## Remaining scientific barriers

A fresh **real** OS/kernel adversarial test on the actual now-pinned local
engine still requires that Docker Desktop Linux Engine be up and the
exact permitted OCI image be cached and independently inspected. Real
model-generated external-task code execution also needs independently
verified image/build provenance and license/SBOM, output quotas,
end-to-end agent/GT compartment isolation and accurate provider token
billing. The available local scorer remains an
`independent-reimplementation`; its equivalence to an official
BIM-Edit evaluator is not established by this PR. The next research
priority is therefore official evaluator provenance/equivalence and
coverage auditing, not silently enabling a 36-task paid model pilot.
