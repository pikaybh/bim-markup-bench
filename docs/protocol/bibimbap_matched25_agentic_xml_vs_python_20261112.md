# BIBIMBAP matched-25 tool-call agentic research harness (Issue #114)

**Date:** 2026-11-12 (Asia/Seoul)
**Code scope:** **Only** separate experimental repository `pikaybh/bim-markup-bench`, isolated worktree `D:\문서\D__1_Projects\202611\bim-markup-bench-issue114-matched-agent`.
**Forbidden scope:** product **BIXML/Xim source, worktrees, schemas, app code, servers, release branches**. No product repository was opened or modified.
**Inference status:** **ZERO new paid LLM/API calls** under this issue. User asked to implement a matched-condition experiment, **not** to authorize a new model-spending budget; the earlier Issue #112 authorization applied only to its completed one-shot cohort, regardless of unused spending headroom.

## 1. What the original paper and code actually did

Primary paper: Kujat et al., *BIBIMBAP: A Benchmark for Instructional BIM-Based Automated Programming*, EC3 2026, [paper PDF](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf), in particular methodology/results, pp. 4–6.

Pinned original author code: [nbharathik/bibimbap](https://github.com/nbharathik/bibimbap), commit `667004e16bd38fd7d538bcee56191465429fd975`, **read-only outside experiment repository**; original dataset [clemenskujat/bibimbap-data](https://huggingface.co/datasets/clemenskujat/bibimbap-data), commit `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`.

The author's `llm_agents/code_execution_agent.py` defines **`execute_ifc_code(code: str)`**, with preloaded `ifc` and `ifcopenshell`, `api`, `util`, `element_util`, `guid`, plus `result` and **`commit()`**. Individual calls allow inspecting the IFC, editing it, receiving stdout/result or Python errors, and retrying. The paper describes up to **25 tool calls per task**. The original benchmark entrypoint copies the source to a distinct working IFC before invoking the model, then scores the final native IFC with the original task-specific `execute_test()`. That allows source-preserving querying and successive revisions; **our previous #112 XML-only experiment was single-shot and therefore not matched**.

The original paper uses several **different model IDs, configuration variants, and repeated samples**; our new paired harness uses **GPT-6 Luna for *both* arms**, 1 sample/task, and does **not** replicate exact paper-baseline model identity, hardware, image or all experiment counts. Published paper numbers are contextual, NOT paired comparisons.

## 2. Prospective, symmetric experimental settings

| Requirement | XML Direct Source-Edit (D) | Python/IfcOpenShell Baseline (I) |
|---|---|---|
| Model | `gpt-6-luna` | `gpt-6-luna` |
| Public question | Exact same original BIBIMBAP question | Exact same question |
| Original IFC | Same external pinned source, independently staged | Same external pinned source, independently staged |
| Tool-call maximum | **25** | **25** |
| Actual tools | `read_building_xml`, `submit_building_xml` | `execute_ifc_code` |
| Iterative observation | Latest valid XML, compile acceptance/error | IFC query result/stdout/exception |
| Author action | Complete replacement of `building.xml` declaration state | Python code to inspect/edit IFC |
| Persist/commit semantics | Successful trusted XML→IFC compile accepts new state and IFC | Explicit `commit()` persists the IFC copy |
| Invalid submission | Returns error; previous valid XML and native IFC **retained** | Returns Python error; prior saved IFC persists |
| Maximum provider output tokens per request | **12,000** | **12,000** |
| Reasoning / sampling | medium / default / one sample | same |
| Retries | **0 automatic provider retries**, failure counts toward budget | same |
| Provider storage | `store=false`, stateless response history replay | same |
| Original benchmark grader | Identical pinned original `execute_test` **after** model run | same |
| Source/result files | Independent scratch per task/arm | Independent scratch |
| Original IFCS | Never modified | Never modified |

**Both arms get equal maximum tool opportunities but deliberately different allowed tool semantics.** The XML arm must directly rewrite a valid full declarative source document; its interface is NOT a command DSL or a Python/IfcOpenShell tool. Only the trusted backend, hidden from the LLM, can compile XML into native IFC.

The Python arm uses an **original-style tool schema and execution globals**, not a copy/paste of the untrusted author's Python execution method on the Windows host. It runs code inside **pinned, local Linux Docker** (see security below).

### Responses API implementation

`tools/bibimbap_matched25_agent.py` implements a real `responses.create` function-call continuation loop. It stores conversation history with model-returned tool calls, executes the allowed tool inside the current arm, appends `function_call_output`, continues up to the 25-call cap and stops on ordinary final response, incomplete response, budget failure, tool cap or provider error. It **does not** feed original author test scores or hidden targets back to the model. Full raw transcript/inputs/feedback and hashes are stored only locally under ignored `results/`.

- Hard 25-call dispatch: a response containing >25 calls cannot cause a 26th execution.
- Multiple provider messages are allowed, with the same maximum output and decoding settings.
- Per-token cost tracking is cumulative; prior priced model charges cannot be reused as new approval.

## 3. Actual experimental-only XML and imperative tool behavior

**D XML**: `tools/bibimbap_matched25_tools.py :: XmlSourceEditSession`

1. Load original IFC4X3; normalize original millimetres to XML metres.
2. Project supported source entities into experimental `urn:bim-markup-bench:toy:v0` XML.
3. Give LLM `read_building_xml()` and `submit_building_xml(xml_text)`, no BIM command bus, no Python tool.
4. For each attempted XML text, store exact bytes in isolated attempt evidence; run trusted security validation and original XML→native IFC compiler. On success store candidate, restore original IFC units, advance valid XML state. On failure return compiler error without losing previously accepted state.
5. Only the **last accepted native IFC** is scored after the model stops. If none accepted, the original source clone receives the same author no-op scoring as the Python arm.

**I Python**: `PythonIfcCodeSession`, `DockerIFCExecutor`, trusted `bibimbap_docker_ifc_code_worker.py`.

1. Stage original source in a unique writable scratch directory. Original dataset and original evaluator Python remain **unmounted**.
2. Execute each submitted `execute_ifc_code` snippet in the pinned image ID `sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee`, Python 3.12.16, IfcOpenShell 0.8.4.post1.
3. Docker restrictions: **`--network=none`, read-only root, non-root UID/GID 65534, all Linux capabilities dropped, no-new-privileges, IPC disabled, PID 32, RAM 768 MB, CPU 1, tmpfs /tmp, two allowlisted mounts** (isolated per-call IFC scratch writable and trusted worker script read-only). Docker engine is pinned to **local Docker Desktop Linux** rather than a possibly remote injected context.
4. The worker provides original paper-style Python globals `ifc`, `ifcopenshell`, `api`, `util`, `element_util`, `guid`, `commit()`, `result`; stdout, stderr and exception feedback. Only `commit()` modifies the persistent task-local copy. The next code tool call reopens that copy.
5. At the end, the source clone or last committed native IFC receives the original author's independent scorer. **Model-generated Python is never exec'd or imported on the Windows host**.

Original author code itself remains **unmodified**. Original user's owned synthetic Docker image is reused, not a mutable/latest public tag.

## 4. Honest limitations of "same conditions"

This is a **matched opportunity/iteration harness, NOT yet a fully matched functional BIM backend**.

Previously measured frozen XML source projection: **36/45 original inputs projectable**, **9/45 unsupported** (IFC2X3/IFC4, tilted/mapped/boolean geometry). Even on projectable inputs, **21/35** previous one-shot LLM outputs failed the experimental compiler's limited native IFC mutation implementation. New 25-call feedback may improve error recovery **but cannot make unsupported mutations available**. The Python reference arm exposes general-purpose IfcOpenShell and thus has much broader creation/relationship/deletion coverage. The matched harness **must report this backend disparity** and is forbidden from claiming the 45-case end-to-end results are a pure comparison of XML vs Python authoring efficiency until backend coverage is extended **in the experimental repository only**. Full strict independent native IFC correctness/clash nonregression is also **not yet verified** across 45 tasks.

Comparability tiers must be labeled separately:

- **Matched model/turn/feedback:** Implemented. Both arms same GPT-6 Luna, original 45 public tasks, 25 tool calls, one sample, original author grader, no provider retries.
- **Matched runtime/IFC feature support:** **NOT IMPLEMENTED / NOT VERIFIED**. XML partial projection/compiler has the limitations above, and compilation currently happens in trusted Windows test runtime while Python executes in Linux Docker. This is documented, not concealed.
- **Matched original published model/harness:** **NOT established**. The cited paper baselines use different models, a separate LangChain agent harness, and different operational environments.

The experimental result report stores **original-author continuous score** separate from **1.0 full marks** and explicitly marks **full independent strict task success as NULL**. Unsupported/failed cases receive zero in 45-row ITT metrics, while actual no-op/partial scorer effects remain traceable. Full 45-case and selected-subset metrics are never mislabeled as the same denominator.

## 5. What was verified now without paid calls

- 45 original task IDs and IFC SHA/provenance checked; 36 previously projectable, 9 previously blocked; **zero LLM calls**.
- Complete XML state read/submit and semantic compiled IFC from a **developer-authored fixed offline fixture**; invalid XML before and after a successful compile leaves last valid IFC intact.
- Live restricted Docker image in use, original IFCS cloned and opened in container; `execute_ifc_code` queries return model-visible `result`, `commit()` persists, and the next separate sandbox call can inspect that saved state.
- Deterministic **fake model** runs multiple function-call turns with feedback, and rejects a 26th tool call.
- Both arms can execute against the **same original public `test_05`** and return actual pinned original-author results under fake-model fixture input. This is **only an engineering integration test**, not a new measured GPT-6 Luna benchmark result.
- Negative cases: invalid XML rollback, unsupported IFC schema, invalid Docker image/tag, duplicate task, missing approval/budget, stale tariff, no real-provider call without budget.
- Reports: `reports/bibimbap_matched25_public_preflight_20261112.json` (no model inference).

## 6. Offline commands and future live authorization

On connected Windows 11 PC, with test venv and pinned author/data directories:

```powershell
$base='D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue114-matched-agent')
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$author=Join-Path $base 'bibimbap-author-upstream'
$data=Join-Path $base 'bibimbap-author-data'

# no API requests and no costs
& $py -m tools.bibimbap_matched25_cli --preflight --author-repo $author --dataset $data
& $py -m tools.bibimbap_matched25_cli --smoke --author-repo $author --dataset $data
& $py -m unittest tests.test_bibimbap_matched25_protocol -v
```

To execute **later, only after a NEW, explicit owner cost/paid-call approval**, copy `configs/bibimbap_matched25_approval.example.json` into a local ignored authorization file, confirm the **current official price**, set `approved=true`, exact requested budget `cap_usd`, the timestamp and identical frozen model/call settings; the code fails closed if any required field, model, rate, provenance, timestamp or fresh one-shot run path mismatches. Do **not** commit the approved authorization file or API key. The already consumed Issue #112 $1 authorization **does not authorize** this paired study.

```powershell
# TEMPLATE ONLY — DO NOT RUN WITHOUT NEW PAID APPROVAL
# & $py -m tools.bibimbap_matched25_cli --run-approved --author-repo $author --dataset $data `
#   --approval (Join-Path $base 'your-fresh-local-approved-budget.json') `
#   --run-dir 'results/UNIQUE_PAIRED_RUN_DIR'
# For one fully matched diagnostic pair, additionally pass --task-id test_05
```

Each paid run path is issued once and cannot be reused; the durable per-request budget ledger pessimistically reserves the next request's maximum input+output tariff **before billing**. Unknown API usage is charged as fully reserved to protect the cap; no auto retries. The maximum of **25 tool calls per task** potentially requires many provider requests per task, so **do not extrapolate the old $0.0527 one-shot cost** or assume $1 covers 45 paired tasks. Final invoice reconciliation remains a separate step.

### Required before claiming paper-comparable *performance*

1. Bring **experimental-only** XML source/IFC backend to all 45 original tasks or explicitly use a preregistered common-capability subset with all exclusions visible.
2. Run full native geometry/relationship preservation and strict success oracles, independent of the original author's fractional update scorer, offline first.
3. Obtain new owner budget approval and run both arms against **the same GPT-6 Luna** with immutable model/tool/context settings, record per-task raw traces and all denominator failures.
4. Compare paired **same-model** XML vs Python outcomes; cite the published paper baselines only as an external reference, not equivalent model/harness measurements.

**Never** use model-generated scripts outside Docker, modify original BIBIMBAP author code, or access the BIXML/Xim product implementation.
