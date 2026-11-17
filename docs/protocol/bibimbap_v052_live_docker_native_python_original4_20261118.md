# v0.52 — LIVE pinned Linux Docker original IFC Python execution attested

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/219
**Frozen base:** v0.51 Draft PR #218 at 234ad85221272bbce8e226e3cf7dfe88a95b062b.
**Scope:** BIBIMBAP original-public source-native IFC research only; NOT Xim/BIXML product, not a fully implemented BIBIMBAP benchmark, not an LLM-model benchmark or causal D/I result.

## What changed since v0.51

On the connected Windows research host the Docker Desktop executable was present but both backend/service and Docker WSL engine were stopped. The installed Docker Desktop application was launched normally, without any Docker settings edits, image pulls, builds, cross-server routing, network access to a model provider or other configuration changes.

The LOCAL fixed Docker endpoint npipe:////./pipe/dockerDesktopLinuxEngine responded with Docker Server 28.3.2 / OSType linux. The pre-existing original pinned benchmark worker image sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee was already present, exactly matching the digest, linux/amd64. The initially untouched v0.51 real session successfully ran a pinned container Python edit for original geometry_test_14 and independently accepted its source-native result.

The next attempted task showed a **real runtime admission false-negative**: the frozen v0.51 admission calls slow Docker info with a strict 12-second subprocess timeout; an independently timed Docker info response took **17.38 seconds**, despite Docker version and exact image inspect being responsive (~1–3 seconds). v0.51's BLOCKED_RUNTIME gate correctly rejected that call before executing any Python.

New tools/bibimbap_v052_live_original_native_python_session.py preserves every v0.51 source/report byte, and uses a separate live v0.52 strict production session. Its admission verifies fixed platform-local Docker Server.Os=linux using **read-only docker version** (no remote host selector), then exact local image digest by read-only docker image inspect; both remain fail closed on missing daemon, non-Linux engine, unpinned image, malformed reply or subprocess timeout. It never starts/restarts Docker, downloads or substitutes an image. The accepted executor remains EXACTLY the v0.51 pinned DockerIFCExecutor with real container creation/HostConfig attestation: no network, read-only container root, cap-drop ALL, no-new-privileges, UID:GID 65534:65534, 768 MiB, 1 CPU, 32 PIDs, allowed tmpfs and **only two host mounts** (expendable /workspace and read-only /worker.py). The model-facing two I-arm tools/read source schema, 25-call budget, IFC checker and frozen input bytes remain the same.

**This code change does not bypass security to defeat the timeout.** It replaces an unnecessarily large read-only local health query with equivalent stronger local OS and SHA binding, and keeps the existing container attestation step which independently checks actual spawned container HostConfig before running code.

## Original four genuine Docker execution evidence

A separate developer-only module, tools/bibimbap_v052_live_docker_controls.py, constructs normal general Python/IfcOpenShell code using **only public source IFC data/question text**, no hidden GT/author grader, no D XML NativeEditPlan or v0.45 typed command writer. These are trusted developer-designed *test controls*, **NOT model-authored LLM submissions**. Each control is submitted to the real model-facing execute_ifc_code API, actually executed by the pinned Linux Docker worker with the real original IFC4X3/native-mm source clone, explicitly commit()s the changed IFC, and must pass the independent v0.51 source-native physical/scope oracle before the session accepts it. Reopened actual IFCs are evaluated by the separate v0.48 public-source research semantic oracle outside the sandbox.

The original public 45 editing tasks, 31 source IFCs, their exact original source bytes/question SHA pins, and the original author grader are unchanged. Exact four previously engineered, nonrandom original sources:

| Original task | Actual native Python source change | Independent physical task predicate |
| --- | --- | --- |
| geometry_test_14 | Strictly increase exactly one original Slab X/Y native rectangle dimension; two different magnitudes | one positive square / one negative nonsquare |
| geometry_test_15 | Move exactly one original Column in world XY, transforming to original parent-local frame; two destinations | one positive 4-corner rectangle / one negative misplaced column |
| topological_test_11 | Change actual shared mapped extrusion depth of both original native Columns based on original question-named Slab world geometry | one positive true top-contact / one negative partial gap |
| topological_test_17 | Remove original storey-unrelated Columns using real ifcopenshell.api root.remove_product | one positive five-column removal / one negative four-column partial removal |

Each positive and negative produces a NEW actual native IFC from actual Docker worker; 8/8 native-source preservation/scope oracle PASS. The v0.48 research-defined physical semantics accepted all four POSITIVE and rejected all four NEGATIVE. This distinction proves the independent native mutation oracle does not mistake a physically valid edit for solving the original question. Container result returned actual uid=65534, gid=65534, worker read-only mount present and source scratch clone visible. The original public IFC bytes remained unchanged. The user-visible model tools do not return private target suggestions or original scorer grades.

## Six actual Linux container security/transaction probes

All six probe submissions ran through the real pinned Docker worker, **not** a copied-IFC offline double.

1. Edit native Slab without commit(): Docker code runs, worker status=ok/committed=false; host rejects.
2. Edit, commit(), then raise an exception: Docker worker status=error/committed=true; host rejects the already-written result.
3. Edit original Slab plus insert unauthorized IfcWall Root: worker status=ok/committed=true; independent native source scope oracle rejects.
4. Commit source without changing anything: worker status=ok/committed=true; source-native no-op oracle rejects.
5. Edit original Slab with live OS isolation witnesses, then commit: worker status=ok/committed=true; host accepts only because independent IFC oracle passed. Live inside-container witness confirmed nonroot uid, read-only /usr/bin, writable isolated /workspace, readable read-only /worker.py and absence of a private grader mount.
6. Transactional real rollback: first real Docker Slab edit accepted; second real Docker call attempts unauthorized IfcWall insertion and commit(); independent native oracle rejects second result and **retains the byte-identical first accepted native IFC**. Original source IFC unchanged.

Five intentionally invalid transactions were rejected, one live sandbox witness was accepted after independent IFC validation. The host never translates an error into a successful IFC commit. A worker status=ok and a commit flag are **insufficient** without real native source physical preservation.

No adversarial test contacts an external network endpoint, changes the Docker host, accesses hidden GT or original grader, touches private production data or invokes paid models.

## Experimental identity, controls and honest exclusions

Primary scientific arms are **D-state declarative XML direct final state diff** and **I-native actual Python/IfcOpenShell executable code in OS-isolated container**. v0.50 provided source-original D-state implementation. v0.52 now proves actual I-native runtime execution for the exact same selected four original IFC sources. All four initial D and I model-facing source XML bytes are identical (source STEP/metadata/world geometry/managed states) and both expose 25 total tool calls. Model-facing **editing** commands are intentionally different, so this alone does not establish equal provider token budgets, equivalent edit authority for all original 45 tasks, equal failure feedback, unbiased fixed prompt, correct author-scorer provenance or a causal model-performance estimate.

The developer control code's source-derived solutions are **not supplied to any LLM prompt or counted as an LLM success rate**. No LLM-generated code trials, no paid provider, no original author benchmark official score, and no hidden GT. Four engineered source cases are exploratory; remaining **41 original public tasks were NOT attempted**. No original source IFC, question definition, prior results, v0.51 frozen report, or research main changed.

## Frozen evidence and offline reproduction

Actual pinned-Linux-Docker live audit: tools/audit_bibimbap_v052_live_docker_native_python.py
Frozen report: reports/bibimbap_v052_original4_live_docker_python_attestation_20261118.json
**Report SHA-256:** 83aaebf382ddad136ee55ff4e3b54559e6630b64587c4665f447bb12baffcc31

The full report captures the original/source question hashes per task, exact D/I initial source equality, actual executable Python code SHA, actual native IFC candidate hashes, native source oracle/independent research semantic verdicts, witness Linux backend, 6 Docker security probe statuses and previously accepted candidate rollback SHA. It deliberately does not store developer solution values, target GUID choices or full generated native IFCs. Previous frozen report SHA v0.50 eb6bef852eabf12ed76b5c5df861a8e5a355a5142e5ad0d3732d646b25dfb28a and v0.51 4ad4a86c00c147523eb65d793cdcbd303a267acf19fb47d26106bb10a1be074d remain unchanged.

The first report is exclusively created (--write). The --check mode **actually re-executes 8 Docker developer controls + 6 live security probes** and must reproduce exact frozen report bytes, not simply compare existing JSON or trust prior claims.

Historical regression note: the prior v0.51 test_28 had a host-state-dependent exact-report equality assumption. Starting Docker correctly changes that particular prior audit's live runtime verdict while its archived report remains intentionally immutable (historical status BLOCKED_RUNTIME). This checkpoint updates **only the old v0.51 test assertion**, not v0.51 runtime implementation/report: it requires the only normalization to be a positively attested *historical BLOCKED to current RUNTIME_ADMITTED* status transition, independently checks zero earlier model executions, and compares every other full report field byte-for-byte. No retroactive evidence rewrite or hidden regression skip. On disconnected future hosts it intentionally fails closed instead of falsely displaying "PASS"; that is expected until the original exact pinned runtime is admitted again.

Reproduce (from isolated v0.52 worktree) with existing Windows research Python venv and the exact pinned LOCAL Linux Docker worker image available:

    python -m tools.audit_bibimbap_v052_live_docker_native_python --check
    python -m unittest -q tests.test_bibimbap_v052_real_docker_native_python

A separate v0.45–v0.52 nonpaid regression suite covers all original source-native reader, typed controls, independent physical oracles and two actual representation runtimes.

**Next priority:** prospective paired D/I LLM study protocol: freeze source prompt, model snapshot, provider token budget, official author grader access/provenance, per-task random order/seeds, first-attempt and feedback budgets, data rights and pricing before any paid trial. No autonomous model calls or statistical claims from developer-controlled edit success.
