# v0.56 — Full declarative XML output feasibility, lossless stream transport and source-license/token admission

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/227
**Stacked parent:** v0.55 Draft PR #226, exact HEAD \`6c55ffd7d6ed734b98cf9f7ecab500a7889f96b6\`.
**Status:** original-public IFC4X3/mm developer-output feasibility demonstrated; **actual paired LLM study still BLOCKED**. Independent BIBIMBAP research only, NOT Xim/BIXML product. Research main/old reports/source IFC/author scorer/GT unchanged.

## 1. The material primary-arm output asymmetry

The actual genuine D-state session v0.55 receives an original source XML with a large immutable STEP/GUID/relationship/mesh subtree and a bounded final-state \`ManagedElements\` overlay. To edit it, the model must submit a COMPLETE modified XML document, including the unchanged source subtree. The true I-native tool instead accepts general Python/IfcOpenShell source executed by the pinned Linux Docker worker.

We measured actual UTF-8 bytes for the four exact original IFC sources and **both** source-derived developer positive/negative controls of each of four original engineering-selected tasks; no LLM or provider was involved:

| Original task | Initial D/I source XML bytes | D COMPLETE final XML bytes (positive) | I developer Python code bytes (positive) | D/I edited text size ratio (positive) | UTF-8 chunks (8192B max) | Stream calls incl. source read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| geometry_test_14 | 39,611 | 39,602 | 887 | 44.65x | 5 | 6 |
| geometry_test_15 | 60,856 | 60,846 | 1,687 | 36.07x | 8 | 9 |
| topological_test_11 | 172,424 | 172,420 | 1,634 | 105.52x | 22 | 23 |
| topological_test_17 | 151,968 | 151,758 | 1,136 | 133.59x | 19 | 20 |

The negative developer controls give essentially the same large disparity. Original one-shot D tool schema (JSON UTF-8 bytes) = **1324**; old genuine I-native tool schema = **1255**; new experimental D stream schema = **1746**.

**Do NOT turn these into claimed provider token numbers.** The research Python environment has no \`tiktoken\`/\`transformers\`/\`tokenizers\` tokenizer installed and no provider/model snapshot was selected. The number of UTF-8 bytes is not the provider's billed input/output tokens; neither current model context limits, tool-call wire overhead, per-message output token limits nor actual prices have been measured. An illustrative 4k/8k-token cap cannot be conclusively mapped to bytes without freezing a tokenizer and tool protocol. But the need to return 172k bytes of original immutable XML rather than ~1.6k bytes of Python shows that a naive single-response "equal tools" study is not experimentally comparable.

Even if a stream transport meets the 25-call ceiling, copying the immutable subtree is an error/cost burden. This is a **scientific design confound**: any eventual D vs I performance claim must report representation length, actual provider billed tokens, truncation, error feedback, tool calls and total wall-clock time separately.

## 2. Genuine full-final-state XML streaming transport, NOT a command or patch

A new **EXPERIMENTAL** D-only model-facing session \`WholeStateStreamDirectSession056\` offers:
- \`read_building_xml\`: identical source/read schema and original source XML to v0.55, returns last-COMMITTED XML only.
- \`submit_complete_building_xml_chunk(sequence, chunk_text, final)\`: up to 8192 **UTF-8 bytes** per chunk, zero-based strictly increasing index, explicit final bit; exactly **24 maximum completed chunks** under the shared 25 total calls if one initial read is used. All partial text remains untrusted and has no effect on IFC or current XML. No source content, physical verdict or grader target is returned in partial-chunk receipts.
- On the final chunk only, it concatenates the **whole XML unchanged**, then calls the exact v0.55 complete-final-state XML compiler and **both** independent native IFC source/non-target geometry and IFC4X3 schema-delta checks. Successful validated native IFC candidate and complete XML are atomically promoted. Malformed XML, incomplete/duplicate/out-of-order/oversized chunks, invalid UTF-8, budget exhaustion or a rejected native IFC cannot modify last-good state. The old one-shot submit tool is explicitly unavailable in this version.

This is still a final **state snapshot**, with the original immutable subtree, not XML \`NativeEditPlan\`, typed BIM operation, a Python editing program, or a server-side content-rewrite algorithm. The streaming host simply acts as byte-preserving transport. It does not infer changes until the entire XML is present. Existing v0.50/v0.55 one-shot source grammar and report hashes remain unchanged.

**Important caveat:** this is **NOT** the same tool protocol as v0.55. The new schema is 1746 bytes rather than 1324; the number of tool calls and feedback events is larger, even though the total 25-tool cap is preserved. It cannot be treated as an "identical exposure" primary D/I causal trial merely because the IFC result matches.

## 3. Actual IFC evidence and fail-closed negative controls

On the four exact SHA-pinned original-public IFC4X3/mm inputs, we generated both public-source-derived developer positive and deliberately wrong controls: 8 whole completed XML snapshots. Each was compiled in two independent new local sessions:
1. v0.55 genuine one-shot D-state complete XML transaction;
2. v0.56 experimental chunk-stream D-state transaction, after byte-identical full-source read.

**8/8** chunk streams were reassembled byte-for-byte identically and accepted. Each yielded the **EXACT SAME real output IFC SHA256** as the corresponding one-shot D native result. All 8 introduced **zero new IFC4X3 schema-validator findings**, and every original source IFC SHA was unchanged. The largest 172,420-byte state required 22 UTF-8-safe chunks plus one source read (**23 calls**), under the 25-call ceiling. The other stream lengths required 6, 9 and 20 calls including the first read.

Negative tests proved out-of-order/duplicate chunks reject and reset partial buffers; incomplete streams cannot commit; malformed fully assembled XML after a valid commit preserves both last-good native IFC and XML bytes; an attempted v0.55 one-shot bypass rejects in the streaming variant; unsupported UTF-8 surrogates and too-long chunks refuse, and all failed calls consume budget. There were **zero model requests**, no sandbox Python execution in *this* checkpoint, zero copied original author evaluator answers, and no paid inference. Previous genuine I-native **real Docker execution** remains pinned to the earlier immutable v0.55 report; we do not relabel it as a new v0.56 paired model trial.

## 4. More precise source-data rights evidence, still no model transfer approval

The original BIBIMBAP author code checkout is \`https://github.com/nbharathik/bibimbap\`, Git SHA \`667004e16bd38fd7d538bcee56191465429fd975\`. The local pinned checkout has **no recognized root LICENSE/LICENSE.md/LICENSE.txt/LICENSE.rst/COPYING file**. Do NOT infer the source code is licensed merely because its README links to a missing license file, or infer code licensing from its independently hosted dataset.

On 2026-11-18, a read-only request to the public Hugging Face dataset metadata API at \`https://huggingface.co/api/datasets/clemenskujat/bibimbap-data\` confirmed:
- dataset \`clemenskujat/bibimbap-data\`, current observed revision \`f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca\`;
- \`private=false\`, \`gated=false\`;
- dataset \`cardData.license=cc-by-4.0\`, and a matching \`license:cc-by-4.0\` tag.

**This corrects the prior unknown dataset-card-license status.** The source-data publisher asserts CC BY 4.0 on the dataset card. That declaration alone does not independently establish the publisher's chain of rights for every original third-party IFC asset, the author's code license, the required attribution/provenance for each IFC, or the user's approval to transmit complete source IFC-derived XML to a model provider with specific retention practices. No dataset files or original IFCs were downloaded as part of this metadata fetch. We retain a frozen metadata *observation*, not a false general legal permission or data upload authorization.

## 5. Prospective paired study admission is NOT satisfied

A separate offline-only v0.56 gate holds all real provider configuration fields NULL:
- exact provider, API region/endpoint and resolved model snapshot;
- real tokenizer and maximum per-message output/context tokens;
- original D one-shot vs full-XML streaming version choice and identical/controlled feedback policy;
- provider-billed input/output token counts and hard USD cap;
- timeout/retry/error and turn budgets, multi-seed prospective paired random order and ITT classification;
- original benchmark code provenance vs published-paper official scorer, independent IFC physical/schema and author-repository metric separation;
- original per-IFC provenance/attribution/license due diligence and explicitly approved provider transmission/retention.

The old v0.53 and new v0.56 admission methods refuse a model trial **even if called with an all-true synthetic approval dict**. They contain no API provider client or credential, do no network calls, have no original grader code, and cannot charge a model account.

**Next research decision:** decide whether full 172k-byte immutable-source XML regeneration is a defensible core D-state benchmark at all. A scoped, declarative **complete ManagedElements final-state representation** with a trusted immutable source anchor could reduce repeated output by orders of magnitude while remaining a true final state rather than a command, but that is a **different arm definition** needing a new frozen checkpoint and all corresponding fairness/provenance disclosures. Do not silently switch primary arms or cherry-pick one.

## 6. Frozen reproducibility commands

- XML stream implementation: \`tools/bibimbap_v056_whole_state_stream.py\`
- Whole original-source developer output feasibility/replay: \`tools/audit_bibimbap_v056_full_xml_feasibility.py\`
- Public HF metadata observation, rights and **no paid launch**: \`tools/audit_bibimbap_v056_offline_trial_gate.py\`
- Regression and negative tests: \`tests/test_bibimbap_v056_output_feasibility_and_stream_gate.py\`
- Frozen full XML D-state output report: \`reports/bibimbap_v056_original4_full_XML_response_feasibility_20261118.json\`, SHA256 **09b2435f402fd333cdb048681313b05a180fe751bc641b9a8a774b77d7620849**.
- Frozen rights/paired-token gate report: \`reports/bibimbap_v056_offline_trial_rights_and_output_budget_gate_20261118.json\`, SHA256 **6b8e983a80a88a06f8de9ebefaeee3c52a71231583bbfeb164c05e0c1b17137c**.
- Exact original parent v0.55 live Docker report remains SHA256 **e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c**.

Offline reproduction in isolated Windows worktree using existing original author/data research environment:

    python -m tools.audit_bibimbap_v056_full_xml_feasibility --check
    python -m tools.audit_bibimbap_v056_offline_trial_gate --check
    python -m unittest -q tests.test_bibimbap_v056_output_feasibility_and_stream_gate

\`--write\` creates reports exclusively and never overwrites; \`--check\` reconstructs eight real native IFC developer controls, 8 full XML streams and their native hash equivalence, and verifies exact saved report bytes. Both audits are **strictly local and no paid provider use**. Do not claim a research outcome of D/I model task accuracy from this engineering evidence.
