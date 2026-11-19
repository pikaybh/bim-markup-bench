# G2 Linux Docker OS-isolation evidence — actual Windows Docker Desktop execution

**2026-11-19 · Issue #247 / Draft PR #250 · tested on existing installed Linux container engine, no dataset acquisition or LLM trials.**

## Actual blocker and correction

The existing `src/runner/docker_isolation.py` trusted kernel probe had been pinned to `/usr/bin/python3`, while the locally present, already published research IFC worker image installed Python at `/usr/local/bin/python3`. A real first probe returned `BLOCKED_OS_PROBE_FAILED`. A controlled diagnostic on the existing trusted command revealed the exact OCI error: `exec: "/usr/bin/python3": stat /usr/bin/python3: no such file or directory`.

Instead of creating a new isolated worker, changing the scientific protocol, starting a Docker service, pulling/building a new image, or invoking a model, we modified only the **existing** trusted probe's interpreter selection:

- Default remains `/usr/bin/python3` for backwards compatibility.
- The only other permitted interpreter is `/usr/local/bin/python3`, used by the pinned already-installed IFC worker. Arbitrary paths, shells or injected command strings are **rejected by the policy and CLI**.
- The Docker container's inspected `Entrypoint` must exactly match that selected path *before starting*, in addition to the existing strict `HostConfig`/mount checks.
- Existing `tools/verify_docker_sandbox.py` now supports `--python-entrypoint`; no new runner or second harness was added.

## Actual Linux container and proof

| Property | Verified observation |
| --- | --- |
| Linux Docker Engine | 28.3.2, Docker Desktop Windows host with Linux/WSL2 container runtime |
| Immutable cached worker image ID | `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee` |
| Explicit trusted interpreter | `/usr/local/bin/python3` |
| Docker daemon HostConfig/mount/security checks | **15/15 PASS** |
| Actual Linux container kernel/runtime checks | **15/15 PASS** |
| Host synthetic source bytes unchanged | PASS |
| Host synthetic hidden-reference canary unchanged | PASS |
| Test container removed after completion | PASS |
| Actual model, API calls or external IFC transfers | 0 |
| Production LLM / original 36-task trial approved | **NO** |

The 15 real kernel checks covered non-root execution, read-only mounted input, denied writes, GT path absence, denied parent traversal, absent Docker socket and launcher key, read-only rootfs, denied outbound socket, no effective capabilities, enforced no-new-privileges and seccomp, and enforced memory/PID/CPU cgroups. The 15 pre-start inspections independently asserted the requested container security configuration, including two allowlisted mounts and denied network.

**Frozen actual probe evidence:** `reports/g2_local_linux_docker_kernel_probe_20261119.json`

SHA256: `c7cda6d98623d2c608a2bc4c4f471f6c4c060b6b718dfd50bb6dac85d8dc7790`.

The report explicitly asserts `worker_image_scientifically_approved=false`, `production_scored_python_enabled=false`, `paid_model_pilot_ready=false`, `real_model_provider_called=false`. The evidence is verified by a new hash-frozen test to prevent accidental promotion of a successful **technical kernel probe** into **scientific-study authorization**.

## Additional real Docker negative tests

The already-implemented `src/runner/ifc_worker.py` and `src/runner/generated_candidate.py` were exercised **as they exist**, using the cached identical image, on owned synthetic IFC inputs only:

- Curated worker: trusted native IFC read/edit/reopen plus denied GT access, network and subprocess actions, source immutability, bounded file/directory outputs, wall-time timeout and cleanup — **11/11 worker tests PASS**.
- Owned dynamic candidate: a separately authored fixed synthetic Python code payload was admitted as opaque bytes only for the OWN synthetic IFC, with real Docker execution and separate trusted grading. The negative tests include forbidden reads/writes, invalid/no output, bounded stdout and checker rejection — **10/10 PASS**.
- Trusted OS isolation probe tests: 11 tests passed before the newly added frozen-evidence regression test, with one skipped Windows symbolic-link privilege test; the final test suite rerun includes the newly added test.
- The new offline real-input stager `src/data/pilot_workspace.py` was **not promoted into the live worker**; original public source rights, true independent source-lineage and task grader remain unverified. The older 2026-11-11 report saying that the engine was unavailable is preserved as a historical *then-current observation*, not rewritten to conceal the change of environment.

## Reproduction in same single checkout

```powershell
$env:BIM_BENCH_DOCKER_PROBE_IMAGE_SHA='sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee'
$env:BIM_BENCH_DOCKER_PROBE_PYTHON_ENTRYPOINT='/usr/local/bin/python3'
$env:BIM_BENCH_IFC_WORKER_IMAGE_SHA=$env:BIM_BENCH_DOCKER_PROBE_IMAGE_SHA
.\.venv\Scripts\python.exe -m unittest -q tests.security.test_docker_isolation tests.security.test_ifc_worker tests.security.test_generated_candidate
.\.venv\Scripts\python.exe -m tools.verify_docker_sandbox --image-id $env:BIM_BENCH_DOCKER_PROBE_IMAGE_SHA --python-entrypoint /usr/local/bin/python3 --enforce-live
```

The second command is **expected to return exit code 2 even on PASS**, because `--enforce-live` refuses upgrading this isolated **owned synthetic program proof** into a provider-funded study.

## Unfulfilled research gates

This is real OS/container proof, not a valid inference about the research hypothesis or original benchmark scores. Before any prospective BIM-Edit/BIBIMBAP real LLM comparison, independently verify original IFC asset rights and external provider transfer/retention, all missing original source assets and study-specific ground-truth separation, original-building lineage, matched D/I model context and tool read parity, a frozen independent evaluator, a true sealed study population, preregistration and actual provider cost authorization. An approved real-task worker must verify that **only the specific pilot task's staged files** are mounted for both arms and that the grader is inaccessible to the worker until scoring.

No new repository, worktree, IFC dataset, model API, Docker image download/build, scored pilot task, or external contact was made during this checkpoint.
