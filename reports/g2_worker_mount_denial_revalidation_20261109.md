# G2 #19 / #21 negative-case and isolated-worker revalidation — 2026-11-09

Status: **PARTIAL GATE EVIDENCE; LIVE PILOT BLOCKED**.

## Immutable starting point
- Base `main` HEAD: `7765a37`, clean and synchronized with `origin/main` before change.
- Work branch: `feat/19-worker-mount-isolation-denial`.
- Linux Docker Desktop daemon: native `x86_64` / AMD64.
- Pinned worker image: `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`.
- Pinned blind grader image: `sha256:fb16105fe69bb87f0ab15390a14733e2c734f0f13e774b1767c57f5b296dbf8d`.
- No new image builds, downloads of IFC data, model API usage, or secret inspection.

## Observed offline / real-container results
1. **Independent blind public IFC scorer**, `python -m tools.verify_blind_public_scorer --image-id <pinned-blind-grader-image>`: five frozen controls PASS; reference GT self-check 3/3 (all axes = 1), unchanged source 1/1 strict FAIL, malformed IFC 1/1 zero/FAIL. Metric origin is `independent-reimplementation`, NOT official. No evaluated LLM attempts.
2. **Worker Linux Docker integration**, `PYTHONUTF8=1` and `BIM_BENCH_IFC_WORKER_IMAGE_SHA=<pinned-worker-image>`, then `python -m unittest discover -s tests/security -p test_ifc_worker.py -v`: 12 tests passed. Includes native edit, input immutability, hidden GT, host secret env, process and network denial, bounded output quota, wall timeout, teardown and new Docker prestart negative mount tests.
3. **OWN dynamic synthetic candidate**, `python -m tools.verify_dynamic_candidate --image-id <pinned-worker-image>`: two checks PASS. Both separate worker/grader containers, no hidden GT in worker, candidate script not mounted into grader, expected wall delta only, no paid calls. These are owned fixture scripts, not provider-generated model outputs.
4. **Full offline Python suite**, `$env:PYTHONUTF8='1'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`: **317 tests, OK, 21 skipped, zero failed/errors**, 133.404s. Earlier invocation without UTF-8 failed because the Windows cp949 default cannot decode UTF-8 protocol YAML; this is an environment sensitivity, not a security gate pass. Use UTF-8 mode for reproductions.
5. **OWN paired deterministic D0/XML and I0/Python oracles**, `python -m tools.verify_g1_oracles --output data/revalidation/deterministic_ceiling_20261109_revalidation.json`: six scenarios, PASS_SYNTHETIC_ONLY. This is not evidence of official BIM-Edit coverage.
6. **G1 official coverage gate**, `python -m tools.g1_release_gate --output data/revalidation/g1_324_support_revalidation_20261109.json --enforce`: expected exit 2 / BLOCKED_NO_OFFICIAL_EVALUATION; 246 statically unsupported + 78 source-dependent unverified = 324; verified official engine supported 0.
7. **G3 candidate preflight**, `python -m tools.pilot_preflight`: candidate integrity PASS and no manifest structural problems, but expected exit 2 / BLOCKED_NOT_A_RUNNABLE_PREREGISTRATION. Fixed 36 tasks, 72 arm slots; official model/price/budget authorization absent.

## Code-level security fix
Before this branch, `_inspect_config` counted only bind mounts. A daemon-inspected container with an extra `Type=volume` or `Type=tmpfs` entry could pass the bind-only mount count while exposing an unexpected filesystem. The prestart gate now checks **the total count of all mounts**. Additionally, it requires private cgroup namespaces. Negative mocked Docker-inspect regressions cover an extra named volume, extra tmpfs mount, host cgroup namespace, host-secret env, and mount target substitution.

## Unmet release requirements
- This does **not** authorize live/paid inference, execution of model-generated Python against public IFC, full BIM-Edit scoring, or normative BIXML benchmarking.
- The chosen 36-task sample has only 30 tasks with pinned public source/GT byte and basic native-delta verification; 6 remain. Full 324 source/GT verification is incomplete. Do not silently fetch large datasets or modify the frozen sample.
- Official evaluator metric parity and full task-level D0/I0 engine coverage are not established.
- Model identifier, pricing snapshot, spend authorization and durable billing broker are missing. Pilot release gate remains CLOSED. Official tasks scored: **0**; paid model calls: **0**.

Related GitHub issues: #19 (isolation), #21 (independent scorer). Current code change is scoped to #19; #21 scorer behavior was only independently revalidated.
