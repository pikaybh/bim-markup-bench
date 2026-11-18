# v0.55 — Transactional source-schema IFC admission for genuine D-state and true Docker Python I-native

**Parent issue:** https://github.com/pikaybh/bim-markup-bench/issues/225
**Stacked base:** v0.54 Draft PR #224 at exact Git SHA 6a6e2a7c361934021177dfde6269af8e89aee609.
**Research only:** independent BIBIMBAP original-public native IFC4X3/mm experiments, NOT BIMX/Xim product or a published-paper official score. No research main merge, no old frozen report rewrite, no original IFC/question/scorer/GT mutation and no paid LLM call.

## Why v0.55 was required

v0.54 established an actual author-scoring loophole: in original public BIBIMBAP topological_test_17, low-level ifcopenshell.file.remove on five original Columns yields author-repository execute_test mean score **1.00**, yet produces **25 newly introduced IFC4X3 schema cardinality errors**. Normal independent D-state final XML diff and I-native IfcOpenShell API cleanup each get author score 0.50 but introduce **zero** schema errors. The source itself already has **one inherited** IFC schema finding. Both historical v0.48 independent task-physical predicate and v0.51 source-native scope oracle erroneously admit the raw-remove candidate; a robust host must require actual source-to-candidate IFC schema error delta **before** committing any model candidate.

v0.54 had demonstrated an independent offline/evaluator-only schema gate. v0.55 now actually applies a **new production-only validator** at the D-state and real Docker Python I-native model-facing transaction boundary.

## New production admission boundary

- Pure model host module: tools/bibimbap_v055_production_schema_gate.py. This imports **no** developer solution fixtures, original author scorer, GT/answer target GUIDs, v0.54 evaluator audit code or paid provider client. It calls actual IfcOpenShell validate(express_rules=False) on source and proposed actual IFC4X3 files and compares error (category, attribute, SHA256 of message) multisets. Original source SHA and candidate SHA are rechecked, a source==candidate alias is rejected, and new schema error count must remain zero. The prior v0.51 independent non-target/source physical oracle must *also* accept the candidate. Function returns only bounded no-leak status/error counts and candidate hash.
- Actual D_STATE session: tools/bibimbap_v055_transactional_primary_DI_sessions.SchemaGuardedDirectStateSession055 (additive to frozen v0.50). It offers exactly the old two tool schemas, same initial model-visible source XML, same 25-call budget, same real original-source compiler, same historical independent v0.45 native writer/physical oracle. On submit it writes an ephemeral candidate; both old and new independent host-side checks run **before** modifying last-good output_ifc and current_xml. Any source/edit parse failure, physical-scope error or new schema error returns a bounded generic refusal, removes the invalid candidate file and retains prior native IFC and XML bytes. No hidden target/grade enters the tool output.
- Actual I_NATIVE session: SchemaGuardedLivePythonSession055 (additive to frozen v0.52), uses the exact same pinned local Linux DockerIFCExecutor backend, with exact image SHA256 2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee, non-root 65534 and unchanged per-container HostConfig attestation (read-only root, network none, caps dropped, no new privileges, resource ceilings, exactly two controlled mounts). It stages a clone of last accepted native IFC in a disposable worker directory, permits truly executed general Python/IfcOpenShell code and explicit commit(), then validates the resulting real IFC against the fixed ORIGINAL source. It promotes output_ifc **only after** successful worker status, explicit commit, backend attestation, no new IFC schema findings, independent original-source native physical scope oracle, and unchanged source/candidate hashes. Invalid edited candidate file is unlinked; prior output IFC SHA remains unchanged. A subsequent valid edit can still be accepted from last-good state.
- Original D/I two tool descriptions and public source read are not modified (no retroactive token-schema change). Exactly 25 total calls per arm/task; source initial XML UTF-8 bytes match D/I. The old frozen v0.50/v0.52 implementation and reports are not rewritten.
- Sandbox worker error after explicit commit(), malformed XML/code, unavailable Docker engine, unsupported IFC/unknown source, and no-op are refused; no provider grader path exists.

**Limit:** IfcOpenShell 0.8.4.post1 with express_rules=False checks reported schema attributes, types, inverse cardinalities; it does NOT prove the file is globally valid under all EXPRESS WHERE/UNIQUE conditions, construction topology or BIM semantics. This is an additional independent admission gate, not a replacement for source/physical and external original author metrics.

## Live original four-case evidence — independent developer controls, not LLM results

All 45 original public BIBIMBAP editing tasks and 31 original source IFC SHA256s remain unchanged. The selected 4 tasks remain engineering-selected, **not** a prospective random original sample. Remaining 41 original editing task rows have not been attempted as matched original-source model edits.

Four selected original-public task IDs:

| Original task | D-state developer control | Genuine Docker I-native developer control |
| --- | --- | --- |
| geometry_test_14 | original Slab dimensional final-state edits | actual Python/IfcOpenShell physical Slab edits |
| geometry_test_15 | original one-Column world XY final-state edits | actual Python/IfcOpenShell one-Column XY edits |
| topological_test_11 | original two mapped Column extrusion-depth final-state edits | actual Python/IfcOpenShell shared representation depth edits |
| topological_test_17 | original target-independent public-source Column presence final-state edits | actual Python/IfcOpenShell native product deletion edits |

Each task had a source-derived correct and deliberately wrong-but-physically-valid developer edit. Both edit methods are tested against real source IFCs: **8 D-state and 8 actually Docker-executed Python native IFC candidates, 16/16 accepted only after new schema/physical gates**, zero introduced schema findings on all 16. Separate v0.48 independent public-source research physical task predicate accepted 8 intended positive (4 per arm) and rejected 8 intended negative (4 per arm). The Docker evidence confirms actual pinned Linux worker backend, uid=65534; not an offline copied-IFC double. Both model-visible original source XML bytes and tool schema names remain identical to their respective previously frozen genuine arm versions.

### Real Docker adversarial sequence and transactional rollback

Using original topological_test_17 public source/question to derive applicable target Columns **without private scorer target identifiers**:

1. The production I-native v0.55 call executes Python ifc.remove() on all 5 target Columns inside **real pinned Linux Docker**, and the worker returns status=ok, committed=true. Host returns NativeSchemaOrScopeRejected; rejects candidate and unlinks its scratch IFC; initial output_ifc remains None.
2. A separate direct real pinned Docker worker replay of the *same* developer control proves the native candidate has **25 newly introduced original-source IFC4X3 schema errors**, inherited original issue count 1, 26 total. This is not inferred from the earlier v0.54 Windows-generated negative control.
3. In a fresh true I-native session, first perform legitimate IfcOpenShell API deletion of 4 unrelated original Columns. This native IFC is admitted and its SHA frozen as last-good.
4. Submit executed general Python that performs low-level ifc.remove() of the **last remaining** unrelated Column. Real Docker worker returns ok/committed=true; host refuses and removes that proposed IFC, while the last-good 4-Column-deletion output IFC stays byte-for-byte unchanged.
5. Submit a correct subsequent native IfcOpenShell API removal of that last Column. The real Docker worker executes and its independent original source scope plus schema gate both PASS; a new valid last-good native IFC is accepted. This proves **recovery** after rejection in the same model-facing I session.
6. A fresh D-state direct XML session accepts an original correct edit, then rejects a malformed state and preserves byte-identical prior XML and IFC. A separate developer-only forced validator error proves a D-state compiled native candidate cannot bypass the new gate or update final state before validation.
7. A missing Docker runtime blocks before creating any worker attempt. In another true pinned Docker run, Python commit() followed by an exception is rejected by host despite worker having already written its temporary native output. No source IFC mutates, and no author grader/GT is mounted.

Real Docker worker scratch and native binary candidates are temporary; report stores SHA256s, task IDs, no developer solution code or target GUIDs. A worker returning commit() by itself is **never sufficient** for a user-visible committed IFC.

## No experimental causal claim, paid provider use or rights assumption

This is an engineering test of genuine native editing *implementations*, **not** LLM-generated task success, published paper official scorer parity or a D-vs-I causal representation result. Model-generated runs=0; paid model calls=0; exact provider/model snapshot, output/input billed tokens, budget/price authorization, user data transfer consent and original author/Hugging Face data redistribution rights remain missing. Original author test source remains evaluator-only, never imported into the production-only schema validator or model session; the v0.53 unconditional launch refusal remains intact. The four exploratory tasks cannot establish 45-task generalizability or statistical significance.

## Frozen report and reproducibility

- Production native validator: tools/bibimbap_v055_production_schema_gate.py
- Genuine new transaction sessions: tools/bibimbap_v055_transactional_primary_DI_sessions.py
- Actual full developer-only 4-task Docker + D audit: tools/audit_bibimbap_v055_live_schema_transactions.py
- Production schema/rollback tests: tests/test_bibimbap_v055_primary_DI_schema_transactions.py
- Frozen JSON: reports/bibimbap_v055_primary_DI_schema_guard_live_transactions_20261118.json
- SHA256: **e651a612e718281fa1ecb2741cf29216796be5df6f6d00439894e0b591b0437c**

The immutable report was exclusively created by --write (never overwritten), and --check MUST genuinely re-execute all 8 D controls, 8 real pinned Linux Docker Python controls, one direct real-Docker raw invalid native output, actual sandbox I rejection/rollback/recovery, D state rollback and worker error/security gates; it checks exact frozen bytes. When local pinned Docker is unavailable, the audit MUST fail closed, not silently claim that old Docker output proves today's execution.

Reproduction requires exact original author/data checkout and existing Windows Python/IfcOpenShell research venv; local pinned Linux Docker must be running (no automatic Docker Desktop daemon lifecycle manipulation inside audit):

    python -m tools.audit_bibimbap_v055_live_schema_transactions --check
    python -m unittest -q tests.test_bibimbap_v055_primary_DI_schema_transactions

Check follow-on full regression status independently and do NOT state it passed unless the actual Windows process exit code is observed. Original author/paper score is NULL, original public source/GT and prior reports are unchanged, and no provider API is invoked.
