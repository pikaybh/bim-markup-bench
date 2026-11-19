# First real BIBIMBAP XML-only GPT-6 Luna trial (2026-11-12)

Tracking [#110](https://github.com/pikaybh/bim-markup-bench/issues/110), upstream model-facing firewall [#106](https://github.com/pikaybh/bim-markup-bench/issues/106), and independent native task-core [#108](https://github.com/pikaybh/bim-markup-bench/issues/108).

**This is the first genuine, paid, single-model edit attempt on original BIBIMBAP test_05. It is NOT the 45-task benchmark result, NOT a paired D/XML vs I/Python causal experiment, and NOT a claim about production BIXML/Xim.** The actual BIXML/Xim product repository was not accessed or modified.

## Owner authorization and execution boundary

The owner authorized exactly **one** GPT-6 Luna (`gpt-6-luna`) **test_05** XML-generation attempt with an API cap of **USD 1**. The experimental direct-XML model may only receive a public instruction, public IFC-to-toy-XML projection, and public toy grammar. The original author test source, private target, reference solution, API mutator and ground truth are **not in the model-facing packet**. The LLM was not given Python tools or shell/network access in the tool interface.

The experiment was performed in a separate experimental worktree `D:\문서\D__1_Projects\202611\bim-markup-bench-issue110-first-live`, **never in BIXML/Xim**.

Predeclared call settings:

- OpenAI Responses API, configured and returned model: `gpt-6-luna`, standard/default tier; reasoning effort `medium`; model temperature not manually specified.
- Exactly **one Responses API call**, `store=false`, no tools, SDK automatic retries **0**, `max_output_tokens=16000`, timeout 160 seconds. No iterative feedback, retry, patching or score-dependent prompting.
- Public model-facing packet SHA256: `2a483f97bf36726c2930ed9df8e80e1106f34bde460416a0c0b11fb3ea736959`. No prompt drift at call.
- Official [OpenAI pricing](https://developers.openai.com/api/docs/pricing), checked 2026-11-12: standard short-context USD **0.10 / million input tokens**, USD **0.50 / million output tokens**. Conservative tenfold one-call reservation **$0.0952790**, below owner cap **$1.00**. This reservation is NOT an actual charge or invoiced result.
- Pinned original source IFC SHA256: `9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca`; pinned original BIBIMBAP author grader SHA from issue #102.
- Single-run exclusive local directory: `results/bibimbap_test05_luna_one_shot_20261112_110` (excluded from Git). The runner refuses a second trial or alternative output location. The outcome has **not** been replayed through the provider.

## Real model result — no post-generation modifications

| Recorded measure | Verified observation |
|---|---|
| Provider status | `completed` |
| Actual provider requests | **1** |
| Model-edited XML attempts | **1** |
| Actual input tokens | **4,270** |
| Actual output tokens | **2,836** |
| Usage-based tariff estimate | **$0.001845** |
| Provider invoice reconciliation | **PENDING** |
| Raw model output byte count | **5,507** |
| Exact unaltered model output SHA256 | `fb15728d7c4952878d4424e33003804f92d36f3c86f50d3ee97eb0c1dc7c6d02` |
| Trusted XML→IFC compiler | **Committed scoped IFC4X3 wall edit** |
| Original BIBIMBAP author `test_05` score | **1.000000** |
| Original author metrics | existence 1.0; location 1.0; dimensions 1.0; integrity 1.0 |
| Separate native IFC public-task core | **PASS** |
| Fully independent strict task success | **NOT YET VERIFIED** |

The frozen public task was *"Add a wall with a length of 15m beginning in (0,-10)."* The actual model-generated XML added **one** declarative `Wall` object with start `(0,-10)`, end `(15,-10)`, height `3.3m`, thickness `0.15m`; height and thickness were free variables not constrained by the public instruction. **All original 25 id-bearing XML elements retained their original semantic attributes**, none were removed, no existing attributes were changed, and original relations/non-ID elements and root metadata were unchanged in a separate post-hoc semantic audit. The semantic audit is NOT the original author's score.

After trusted compilation to genuine native IFC4X3 (restoring the source's original millimetre units), the separate author-independent public-task core checker measured **~15.00075 m horizontal world-space vertex span** and a closest start vertex at **0 m**, exactly one added native `IfcWall`, and all existing `IfcRoot` GUID/class identities preserved. The original author binary/continuous score vector independently returned 1.0 on all four metrics. The source-identical negative control for this creation task had previously scored 0.0, and the wrong-length 10m development control scored only 0.75 (not a valid strict edit).

Importantly, **the author score is a real original-author score, not our surrogate or a copied developer-authored positive witness**. The model response, prompt hash, provider usage and output IFC/result SHA values are kept in the independent experiment evidence.

## Evidence custody and reproducibility

Two **Git-safe**, machine-readable reports:

- `reports/bibimbap_test05_luna_first_real_20261112.json`: provider model/status, token counts, estimated cost, exact model text and native-result digests, original author metric vector, independent task-core summary. No API secrets, original third-party IFC bytes, full provider payload or raw model output.
- `reports/bibimbap_test05_luna_semantic_diff_20261112.json`: separate original-vs-edited XML semantic diff from the exact saved model output; **zero extra model calls**, never changes actual model text.

The one immutable original model response and generated raw XML remain **local, intentionally excluded from Git**:

```
results/bibimbap_test05_luna_one_shot_20261112_110/
  model_generated_exact.raw.txt       # exact provider response output, 5,507 bytes
  provider_response_raw.json          # raw provider response payload
  source_normalized_m.ifc             # temporary trusted normalized source
  candidate_result_m.ifc              # actual compiled candidate
  candidate_result_mm.ifc             # converted candidate, native author scorer input
  results_local.json                  # local full report (path details not in Git)
```

All local data and generated model bytes are preserved as run evidence. External third-party IFC and original BIBIMBAP author code remain in their separate pinned checkouts; redistributability is not asserted.

Reproduce the **offline** source audit (NOT the paid inference) from the isolated Windows worktree with already installed Python:

```powershell
$base = 'D:\문서\D__1_Projects\202611'
Set-Location (Join-Path $base 'bim-markup-bench-issue110-first-live')
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
$env:BIBIMBAP_DATASET = Join-Path $base 'bibimbap-author-data'
$env:BIBIMBAP_AUTHOR_REPO = Join-Path $base 'bibimbap-author-upstream'

& $py -m unittest tests.test_bibimbap_real_luna_evidence tests.test_bibimbap_public_gate tests.test_bibimbap_native_core -v
& $py -m tools.audit_bibimbap_test05_real_semantic --dataset $env:BIBIMBAP_DATASET --raw-output results/bibimbap_test05_luna_one_shot_20261112_110/model_generated_exact.raw.txt --score-report reports/bibimbap_test05_luna_first_real_20261112.json
# NEVER repeat --live-approved: this issue's one approved request is already consumed.
```

## Scientific interpretation / next priorities

**Observed:** One real GPT-6 Luna generation succeeded at this one author edit task, with unchanged single-model output and a strong genuine IFC result. This establishes technical feasibility of the **experimental IFC-backed XML projection path** for at least one simple Create task.

**Not established:** overall BIBIMBAP 45-edit task success, all-100 paper performance (55 retrieval tasks), parity with the authors' published model protocols, causal improvement over LLM Python/IfcOpenShell or any Revit/BIXML API, full independent strict success including changes to other opaque original geometry and collisions. No inference about actual BIXML/Xim product implementation. The original author integrity metric passed, but our independent native geometry core has not re-audited full clash/non-target geometry preservation.

**Next:** Validate and preregister task-level independent full strict oracle(s), freeze a separate supported-subset selection without inspecting LLM results, and obtain **new budget authorization** before any further paid provider calls. The already-spent single-trial $1 maximum is not an approval for 44 more requests. All previous P0 results and original 45-row prelaunch candidate ledger remain intact.

The stored provider usage estimate is calculated from official public rates; final invoice and any discounts/surcharges remain unreconciled. No BIXML/Xim code changed.
