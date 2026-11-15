# BIBIMBAP v0.21 — Non-destructive Docker cold-start readiness and original-public regression recovery

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/156

**Stacked parent:** v0.20 Issue #154 / Draft PR #155 at exact commit `dfe7ebfdf731250ddafe5ae483509e4411127dbb`.

**Research identity:** Independent academic BIBIMBAP XML-vs-Python benchmarking, **not Xim/BIXML**. No production services, public dataset, scoring criteria, original IFC, paid model inference, or hidden target data modified.

## Root-cause evidence: transient Docker Desktop engine cold/slow responsiveness

At the end of v0.20 (2026-11-15 KST), a full 11-module regression was NOT green (prior Docker engine timeouts), while the standalone new v0.20 20 tests were green. The frozen v0.19 Python worker's `_verify_local_image` makes a pinned Docker image-inspect call with an **unmodified 12-second timeout**; this may fail if Docker Desktop/WSL2 has just been started or is under load.

The connected Windows research PC was rechecked **without any Docker/WSL/service restarts or file cleanups**:

| Check | Observed |
|---|---|
| Git prior `feat/154-v020-original45-capability-gate` | clean, exact `dfe7ebfdf731250ddafe5ae483509e4411127dbb` |
| Windows Python venv | 3.12.2, lightweight startup `0.313s` |
| IFC parser | `ifcopenshell` `0.8.4.post1`, imports successfully |
| First Docker CLI `--version` | timed out at initial 8-second limit (not proof of Docker corruption) |
| Initial Linux engine `docker info` | timed out at initial 18-second limit |
| Initial exact pinned local Docker `image inspect` | **14.422 seconds**, exited successfully, exact expected SHA |
| Identical subsequent `image inspect`, two reads | **0.750 seconds / 0.281 seconds**, both exact SHA, exit 0 |
| `docker ps` | exited 0, no running containers listed |
| WSL `-l -v` | Docker Desktop and separate Kali WSL distributions were running; neither restarted or modified |

**Assessment:** confirmed a transient Docker command/daemon response latency, including a first read exceeding the historical 12-second threshold. We did **not** prove that cold start is the only cause or that the host will never stall again. Repeated response speed becomes normal after read-only image inspection; no service restart needed to recover this session.

Subsequent fresh actual original-public test rerun, on the **same Windows host and pinned worker image**, passed:
- v0.19 real Docker original-public IFC edit + original scorer and negative kernel restrictions, together with v0.20 evidence-only tests: **31/31 PASS**, 30.066s unittest elapsed, 39.0s enclosing process (2026-11-15 KST).
- v0.3/v0.4/v0.14–v0.20 selected 11-module regression, including v0.19 actual Docker: **150/150 PASS**, 223.016s unittest time, 231.079s enclosing process (2026-11-15 KST). This does **not** claim that the historical whole repository test suite was fixed; its known previous errors are outside this selected run.

## New v0.21 guardrail

`tools/bibimbap_v021_nondestructive_readiness.py` is a **host-only read-only preflight**, not an execution environment or cloud LLM broker. It:
- Anchors calls to the existing Windows Docker CLI, fixed local `npipe:////./pipe/dockerDesktopLinuxEngine` and exact cached immutable image `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`. **No pull/build/create/start/stop/kill/prune/restart**, no new container exec.
- Makes one bounded cold image digest inspection (up to 25 seconds) and one bounded warm repeat (up to 18 seconds); the warm repeat MUST be less than **10 seconds** to leave margin against the frozen legacy 12-second worker timeout. This is a **point-in-time readiness gate**, not a promise of uninterrupted future host availability.
- Checks Docker engine reports Linux, no residual `bmb-v019-sealed-*` Docker containers, pinned original author/data Git HEAD and both source worktrees clean, current IfcOpenShell version pinned. All checks use only read-only `git`, `docker image inspect/info/ps` and `python -c import`.
- Emits a sanitized summary with observed timing and status. It does not emit paths, host credentials, IFC file bytes, native source GUID inventory, scorer/hidden-GT content, candidate script stdout, or a model score.
- Explicitly states that readiness **does not authorize** any real matched LLM trial, paid model call, original author-scored result, representation-only causal claim, or sandbox security certification.
- Fails closed on wrong immutable worker digest, wrong Docker endpoint, wrong engine type, source Git corruption/dirty worktree, unexpected residual worker, unpinned IfcOpenShell or persistently slow/failed image read. It neither attempts nor recommends silently resetting another user's containers/WSL services.

**Actual fresh v0.21 host preflight:** status `READY_FOR_SCOPED_OFFLINE_ORIGINAL_DOCKER_REGRESSION_ONLY`, first read **0.469s**, second **0.109s**, pinned source Git SHA clean, no prior worker orphan. Sanitized report `reports/bibimbap_v021_nondestructive_host_readiness_20261115.json` SHA-256 `a08f7406a73fdf6c0d0b3301256cfcf26c7bb6a02e0d9d998ffc89e454d62fd6`. Unlike deterministic geometry reports, this readiness file contains **observed wall times**, so subsequent cold/warm observations can be valid but byte-different. Do not invent a reproducibility claim for dynamic timing.

## New tests

`tests/test_bibimbap_v021_nondestructive_readiness.py`: **12/12 PASS** (0 failures, 0 errors, 0 skips) in **0.041s** test time; startup/wrapper 0.516s. Includes cold-slow-then-warm-fast recovery, permanently slow warm rejection, wrong local Docker image SHA or engine, source data/author SHA drift, dirty source worktree, mismatched IfcOpenShell, orphaned older worker, missing/invalid/timeout probes, fixed command scope and previous v0.20 frozen original45 evidence SHA validation.

**Important:** the v0.21 unit tests use synthetic `Observation` values to test the gate. The separate v0.21 host preflight was actually run on Windows with real Docker commands; do not call the synthetic tests live OS security probes.

## Scientific limits unchanged

The original 45 public tasks remain **15 create / 15 update / 15 delete**. Original developer-source D0/I0 native byte identity **5/45**, original-author both-arm scoreable **3/45**, two original evaluator reference-source errors, 40 other same-protocol task pairs not evaluated. One v0.19 Docker original public task is a repeated developer example, not a sixth independent matched case.

- Real D/I LLM task trials **0**, paid inference **$0**.
- 45/45 common *read-only* source packet replay equality is **not complete original IFC information parity**.
- All 45 original public IFC sources contain native products absent from the current writable XML typed view (per frozen v0.17); task relevance of those omitted objects **unknown**.
- Complete equivalent native write capability has not been established for all 45 tasks.
- The offline terminal receipt state machine v0.20 is not an integrated real model-host security boundary; the v0.19 Linux container tests are not independent kernel exploit certification. Actual LLM launch **blocked**.

The next independent research checkpoint should investigate *task-relevant original IFC source facts and true D0/I0 native write-operation capability parity* on the original public task denominator, without changing graders or expanding old success denominators. A paid trial requires separately approved model, hard USD cap, external provider security and a preregistered scientific comparison protocol.

## Reproduction

From a Windows research PC with pre-existing local Docker Desktop Linux engine, cached pinned OWN image and original pinned public Git checkouts:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue156-nondestructive-readiness')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# This only makes bounded READ-ONLY Docker/Git/Python probes.
& $py -m tools.bibimbap_v021_nondestructive_readiness `
  --base $base `
  --output 'results/NEW_UNIQUE_v021_host_readiness.json'

# Unit tests do NOT make live Docker calls.
& $py -m unittest tests.test_bibimbap_v021_nondestructive_readiness -v
```

**Actual full v0.21 combined scoped regression (2026-11-15 KST):** 12 explicitly selected v0.3/v0.4/v0.14–v0.21 unittest modules, including the original public-IFC Docker v0.19 worker and original author evaluation: **162/162 PASS / 0 failures / 0 errors / 184.396 seconds unittest / 202.219 seconds enclosing process / exit code 0**. This is a new, independently completed live run; the prior v0.20 Docker timeouts did not recur. It does **not** claim the old whole-repository test discovery is green, a complete IFC XML/native write-parity proof, or any real LLM evaluation success. The separately captured sanitized recovery report is `reports/bibimbap_v021_scoped_regression_and_recovery_20261115.json`. New v0.21 code is purely a read-only host preflight, not an experimental shortcut or modification of existing native IFC benchmark scoring.
