# BIBIMBAP v0.19 — Sealed one-shot ORIGINAL-IFC Python writer, real Docker kernel probes, and independently scored developer witness

Issue: https://github.com/pikaybh/bim-markup-bench/issues/152

**Independent academic research only. NOT BIXML/Xim production code. NOT a real LLM comparison.**

This checkpoint independently extends v0.18 Draft PR #151 (`feat/150-v018-common-read-evidence`, commit `64bac24ec98325219b2d7c94bfe114fe87af46a3`). v0.18 proved byte-identical read-only common IFC source facts / SHA receipts for 45 original public tasks; did **not** secure the Python mutation path. v0.19 implements and actually executes a sealed one-shot Linux-container Python native-IFC edit on **the real original PUBLIC input**, without using a Python interpreter on the Windows host to execute candidate code.

## 1. Actual original source and trusted executable isolation

The connected Windows 11 research PC already has Linux Docker Desktop 4.43.2, Linux Docker engine 28.3.2 with default seccomp and cgroup-v2, and the previously curated **cached image**:

`sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`

The image is a Linux/amd64 **non-root UID/GID 65534** Python 3.12/IfcOpenShell 0.8.4.post1 worker. Its provenance and label are checked by the existing `src.runner.ifc_worker._verify_local_image`, using an **exact immutable sha256 image ID**, NEVER a mutable Docker tag or a pull. This version reuses the previously reviewed `_inspect_config` and `_limited_attach` routines, not the historical OWN-synthetic success label. The old image/worker/source code are **not modified**.

New `tools/bibimbap_v019_sealed_original_docker.py` orchestrates the following security policy from the **trusted host only**:

- Verify the original PUBLIC IFC file's expected cryptographic SHA, real ordinary path and bounded source size (256 KiB for this offline pilot). Copy into a disposable sandbox root; **only the temporary clone** is mounted to `/input`, **read-only**. The original author's dataset and grader are **NOT** mounted.
- Write one **allowlisted developer-owned** Python fixture to a separate read-only `/task` bind. The positive original `test_15` code is generated only from the **original PUBLIC task text**, with no hidden score targets, XML tool, original-author scorer or reference solution in its module imports. Three additional allowlisted fixture source hashes test OS denial, output leak resistance and infinite-loop timeout. **Arbitrary LLM-supplied code is NOT accepted** in this PR.
- Create a Linux Docker container with `--pull=never --network=none --read-only --user=65534:65534 --cap-drop=ALL --security-opt=no-new-privileges:true --cgroupns=private --ipc=none --pids-limit=1 --memory=512m --memory-swap=512m --cpus=0.75`, bounded native RLIMIT, 16 MiB `/tmp` and 64 MiB `/output` tmpfs. **There is no host writable output bind or Docker socket mount**, no network, and **`--log-driver=none`** to avoid persisting untrusted stdout/stderr in Docker daemon logs.
- Verify **actual daemon-created container HostConfig, image ID, read-only mounts, explicit logging driver and non-root settings BEFORE starting it**. Untrusted code executes inside Docker only via the existing trusted image `run_candidate.py`; no arbitrary Python source is executed on the Windows research host.
- Capture candidate stdout/stderr in bounded **host-only memory** with an enforced wall-clock timeout and kill/container removal; never stream candidate output, errors, traceback, source bytes or native IFC to the LLM. Only the bounded IFC artifact is delivered to the trusted host's **separate validation stage**, where independent native IFC-only oracle and original pinned author grader run after the container is stopped/removed.
- On every exit/error/timeout: `docker rm --force` scoped to the specific randomly generated `bmb-v019-sealed-*` identifier and delete all temporary source/code/output files. Original public source file SHA is rechecked. No global service changes, image pulls or database operations.

**Important host/model contract:** the only permitted hypothetical LLM-visible one-shot response is exactly `{\"status\":\"SEALED_ONE_SHOT_SUBMISSION_RECORDED\",\"execution_feedback_available\":false,\"tool_continuation_allowed\":false}`. The host's private native candidate artifact, native hash, scorer result and OS-probe flags must never be serialized into the *same model's* observation/next turn. The module intentionally does **not** implement a real model provider or live `submit` endpoint; future integration must enforce the terminal one-shot contract at the host boundary. A constant receipt alone is not evidence of a fully integrated LLM feedback-suppression service.

## 2. Actual Linux kernel restriction probes on the original public source

Inside the real Docker worker with a copy of original `basic_tasks.ifc`, a developer-authored own negative fixture attempted the following **14 checks**; the host read their boolean results privately and required all to be true:

1. Non-root UID 65534.
2. Original read-only source clone readable.
3. Native input IFC write denied.
4. Candidate source script write denied.
5. Secret/provider environment variables absent.
6. Hidden author ground truth unmounted.
7. Host user path not mounted.
8. Docker socket absent.
9. Outbound external network socket denied.
10. Subprocess spawn denied by PID limit.
11. Read-only root filesystem denied write.
12. Linux kernel seccomp filter active.
13. Effective process capabilities zero.
14. Kernel NoNewPrivs enforcement active.

**Result: 14/14 PASS on real original-source Docker execution**, not a mocked flag-only probe. Kernel attestation here verifies reported Linux process state and observed denial for the tested operations. Linux containers and Docker Desktop daemon are **not** a separately certified VM-grade security boundary against all malicious native code or kernel exploits.

Additional probes:
- A developer-authored fixture deliberately prints a fake private canary and the original IFC prefix to stdout, and then writes a valid IFC. The collector captures output **host-private only**. The only model-visible receipt is an invariant constant with **neither canary nor original IFC/candidate SHA/error/scorer details**. Docker daemon logging is disabled.
- An infinite-loop fixture exceeds the external wall-clock limit and is killed; the unique container is forcibly removed in a `finally` cleanup. Neither the timeout detail nor the exception is exposed to the model channel.
- Tampered source SHA, mutable/tagged Docker image, wrong candidate SHA/unauthorized Python script, unexpected output settings or invalid mount/identity are rejected **before untrusted code execution**.

## 3. Actual original-public source edit and independent grading

The fixed **public original BIBIMBAP `test_15`** instruction requests moving one publicly identified `IfcColumn` by **−3 metres along world Y** in the real `basic_tasks.ifc`, IFC4X3, original length units **millimetres**. The image runs only that original-source/public-question-derived developer Python fixture, using IfcOpenShell native placement update in original IFC millimetre units, then writes a bounded `result.ifc`.

After Docker stops, an independent native IFC-only oracle (`strict_move_column`) confirms exactly one allowed original STEP placement point changed and the actual target mesh moved −3m, with source identities and non-target geometry preserved. The **unchanged pinned ORIGINAL AUTHOR scorer** (`grade_author`) then scores the same artifact. These checks are done by the trusted host, **not mounted into Docker or exposed to a model**.

| Measurement | Verified v0.19 original `test_15` developer-controlled worker |
|---|---|
| OS-isolated source-only IFC4X3 edit | **PASS** |
| Original input unchanged | **PASS** |
| Independent native IFC-only world-geometry & STEP oracle | **PASS** |
| Original author pinned score | **1.0** |
| Linux security denial checks | **14/14 PASS** |
| Host-to-model feedback exposure | **constant receipt, no stdout/candidate/score** |
| Infinite-loop fixture | **timeout and container cleanup verified** |
| Real LLM-generated scripts or paid providers | **0 calls / $0** |

New original scorer result is a **developer-authored existing `test_15` repeat on a different, sealed execution backend**, NOT an additional independent matched task and NOT an LLM agent performance score. Original **all45** 15/15/15 denominator unchanged, previously verified source-only D0/I0 developer edit parity **5/45**, original author-scoreable D0/I0 **3/45**, prior original grader missing-target cases **2**, other same-protocol tasks **40 untested**. No historical results upgraded or silently dropped.

## 4. Remaining scientific and OS-security blockers

The pilot worker is a real Linux Docker process, but no third-party kernel exploit assessment, VM-grade isolation attestation or full native authoring-capability audit has been completed. The I-arm script can compute on the actual source IFC **inside** its sealed invocation, so it still has computational access to source semantics the limited D-arm XML projection might not represent. No iterative stdout/error feedback is given to the authoring LLM in this prototype, but complete *pure representation* information equivalence is **NOT established**.

This issue does NOT turn on arbitrary generated Python or real LLM models, does NOT merge code to main, and does NOT modify prior scorer/data/hidden targets. Before genuinely comparing XML vs Python LLM:
- Choose a preregistered scientific estimand: **descriptive unequal-system comparison** vs **strict information/capability controlled representation trial**. If the latter, the D-arm and I-arm must be audited for equivalent task-relevant source information, native writing ability, and all post-execution feedback; the current 45-task common fact packet is not enough.
- Independently review OS isolation/worker image source-to-image provenance and lifecycle including malicious unknown Python, not just allowlisted developer probes. Enforce one-shot terminal model interaction in a real host broker, not a stand-alone constant function.
- Preserve author/scorer anomalies (two broken Window references, Column `test_16` integrity disagreement) and historical full 45 task denominator; no grader patch to inflate scores.
- Approve a specific **paid model, request/token/USD hard cap and study protocol** before any new real LLM experiments. No API calls or paid tests are authorized in v0.19.

## 5. Evidence and reproduction

- Author source HEAD: `667004e16bd38fd7d538bcee56191465429fd975`
- Public data HEAD: `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`
- Previous pinned v0.18 common-read audit SHA: `89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a`
- New sanitized `reports/bibimbap_v019_sealed_original_test15_os_and_author_20261114.json`: SHA-256 `5a49f85e74398269ad5a094db9ec362fe9ed4658a89028a68b3c08452059075e`. No raw IFC, no full original target GUID list, no model-generated code or secret included. No original data copied into Git.

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue152-sealed-native-ifc-writer')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v019_sealed_original_docker -v

# Actual original IFC + Linux Docker process. Always use a NEW output path.
# The image MUST already be locally cached with its exact SHA; no image pull.
& $py -m tools.audit_bibimbap_v019_sealed_original `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --prior-v018 'reports/bibimbap_v018_original45_common_read_observation_audit_20261114.json' `
  --output 'results/NEW_UNIQUE_v019_sealed_original_evidence.json'
```

**Actually verified new v0.19 tests:** `python -m unittest tests.test_bibimbap_v019_sealed_original_docker -v`: **11/11 PASS / 27.071 seconds / exit 0**, including a *second live* Docker original-source audit and byte-exact JSON comparison with the frozen report. Owned source code in the actual Docker OS probe was sanitized to contain no user's real host-home path; original security checks remained 14/14.

**Actually verified combined scoped regression:** `python -m unittest tests.test_experimental_v4_slab tests.test_experimental_v3_column_crud tests.test_experimental_v14_native_window_delete tests.test_bibimbap_v14_original_hosted_d0 tests.test_bibimbap_v015_i0_source_parity tests.test_bibimbap_v015_fixture_admission tests.test_bibimbap_v016_scoreable_column tests.test_bibimbap_v017_topological_slab_and_information_gate tests.test_bibimbap_v018_original_common_read tests.test_bibimbap_v019_sealed_original_docker -q`: **130/130 PASS / 130.297 seconds / exit 0**, 10 selected test modules only. No old baseline modification.

**Adversarial review:** exactly 5 new `v019` source/test/report/protocol files staged; full original hidden Window grading GUID literal scan of 8 targets across all new files PASS (0 leaks); credentials and host-personal-path scans PASS (0 leaks). Docker `ps -a --filter name=bmb-v019-sealed-` shows no orphan containers after the actual run, including an infinite-loop case. Git CRLF-aware whitespace scan PASS.

**No previously frozen reports, original-source IFC, scorer files or user host services were modified.** Historical full repository 832-test discovery was not green, and passing a focused regression does not claim otherwise.
