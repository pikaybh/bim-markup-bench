# G2 original BIM-Edit pilot INPUT-to-Linux-container mount proof

**Date:** 2026-11-19 · **Repository:** `pikaybh/bim-markup-bench` · **Issue:** #247 · **PR:** Draft #250. This extends the **existing** `src/runner/docker_isolation.py` and `tools/verify_docker_sandbox.py`. No additional repo, worktree, runner service, dataset acquisition, model inference, or original scorer.

## New result: actual pinned BIM-Edit task input, not a synthetic substitute

The fixed BIM-Edit 36-task *candidate*, which remains unpreregistered, has 25 original input paths; 20 existing sources have direct content SHA256 and publisher Git/LFS verification, covering 30/36 tasks. Six tasks remain unready due to five absent original inputs. The previous G2 kernel proof used a synthetic marker; this second G2 proof tests **the exact original task input staging and Docker mount boundary together**.

A trusted predeclared selector chose original public task `COL-DEL-SPA-A-001` because it is a cached/verified input whose public filename/path also serves as a reference in a different original BIM-Edit task (the cross-task reference-alias risk). This IFC is accessed *exclusively in the selected task's input role*, by hashing opaque bytes without native geometry parsing, result editing or reference scoring. The original source content SHA256 is `88de67de1f28a64ce0f1ca7eb330a129178ae7a97f52cdeddf0bc1de033cc0a3`. The original source is not committed into Git.

Three separate disposable workspaces were staged, one each for `D_FULL`, `D_MANAGED` and `I_NATIVE`. Each contains **exactly** `input.ifc` and the sanitized `task.json` with fields `task_id`, `instruction`, `input_file`. All three workspaces supplied the **identical SHA256 input** and **identical SHA256 task instruction** (payload SHA256 `e1246948333cbc12613d854b4b29b017feee720ee3aa75514d49faca261a8fc7`). The input IFC is not copied elsewhere except for these temporary local workspaces. No model ever reads these files.

## Actual Docker checks

| Evidence field | D_FULL | D_MANAGED | I_NATIVE |
| --- | --- | --- | --- |
| Container creation PRE-start checks | **17/17** | **17/17** | **17/17** |
| Linux kernel and task file checks during execution | **22/22** | **22/22** | **22/22** |
| Original source SHA256 unchanged after container | YES | YES | YES |
| Sanitized task payload SHA256 unchanged | YES | YES | YES |
| Runtime executed model-generated Python | NO | NO | NO |

The 17 pre-start checks include the original 15 Docker HostConfig security assertions **plus** exact host mount-source-path origin and exact two allowed public SHA256 environment values. These additional assertions prevent a malicious or accidental bind of a different task or real GT directory into the same `/input` name. The Docker-created container is inspected **before** being started and is refused unless all checks pass.

The 22 actual runtime checks include the original 15 kernel security assertions (nonroot 65534, denied write to immutable input/readonly root, no network, no Docker socket or provider key, no GT paths, no capabilities, no-new-privileges, seccomp, PID/memory/CPU cgroups), **plus seven source-only and task-file checks** (exact two files, expected task payload SHA, only approved instruction fields, task file readonly, other task absent, full dataset absent, reference IFC absent within task directory).

Synthetic **OWN** canaries for separate reference, other task and full corpus were created outside Docker mounts, kept unchanged and deleted. **No actual GT IFC was opened in its ground-truth role.** Input/reference aliasing is disclosed, not ignored: a byte sequence permitted for task A as input may be the reference for task B in benchmark metadata. Cross-task model memory and original-building shared lineage remain separate experimental risks. Mounting only the selected task is necessary but not a proof of uncontaminated LLM weights.

All container names were unique under existing `bim-bench-probe-` namespace and forcibly removed after execution. Temporary staged IFC copies were deleted by the local temporary directory context. No test Docker container was left behind.

## Pinned real evidence and repetition

- Machine evidence: `reports/g2_bim_edit_pilot_docker_input_mount_20261119.json`.
- SHA256: `3f1b2313b285edf6e2fd6a57bc1f608fd6e5cf6c0624b835ea8511f9cbf39dd6`.
- Local cached Linux image ID: `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`.
- Docker Engine: `28.3.2`, Python entrypoint `/usr/local/bin/python3`.
- Offline test: `tests/security/test_pilot_docker_mount.py`. It exercises 17 prestart, 22 runtime, malicious swapped GT/other mount origins, extra mounts, fake SHA env, unauthorized generated program/entrypoint, extra secrets, accidental privileged and networked containers, exclusive-write and anti-release outcomes. A pinned evidence hash prevents silent overwrite or reinterpretation.
- The existing G2 synthetic kernel report remains unchanged: `reports/g2_local_linux_docker_kernel_probe_20261119.json`, SHA256 `c7cda6d98623d2c608a2bc4c4f471f6c4c060b6b718dfd50bb6dac85d8dc7790`.

Reproduce in the same existing Windows checkout without an Internet IFC download, Docker image pull or LLM API:

```powershell
$env:BIM_BENCH_DOCKER_PROBE_IMAGE_SHA = 'sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee'
$env:BIM_BENCH_DOCKER_PROBE_PYTHON_ENTRYPOINT = '/usr/local/bin/python3'
.\.venv\Scripts\python.exe -m unittest -q tests.security.test_pilot_docker_mount
.\.venv\Scripts\python.exe -m tools.verify_docker_sandbox --image-id $env:BIM_BENCH_DOCKER_PROBE_IMAGE_SHA --python-entrypoint /usr/local/bin/python3 --pilot-stage-input-mount --enforce-live
```

The second command **must return exit code 2 even though the safety probe itself passes**; `--enforce-live` preserves the full-study launch refusal.

## Distinctions and remaining hard gates

**Verified:** 3× local Docker mount and real-kernel task isolation for one already-cached original input, 36-task denominator unchanged, both arms identical source/prompt bytes, GT/other task/whole source corpus not mounted, immutable image/HostConfig/mount path and hashes verified, fixed trusted probe only.

**Not verified or permitted:** Python **generated by an actual model** editing these official inputs; D arm's declarative XML projection equivalence or managed coverage; network/API/provider use; verified per-IFC source creator and transfer rights; independent original building lineages; five missing input IFCs/six unready task rows; genuinely unseen holdout; hidden-GT assessor isolation for official tasks; author-equivalent official scoring, or approved owner/model/cost/attempt preregistration. The live runner must stay disabled for original LLM trials. This technical positive must **not** be reclassified as scientific progress on measured D/I effects or as a BIM-Edit official score.
