# BIBIMBAP v0.31 — Original45 task-specific source/write comparability gate

**Issue:** [#177](https://github.com/pikaybh/bim-markup-bench/issues/177)
**Parent:** [Draft PR #176](https://github.com/pikaybh/bim-markup-bench/pull/176), immutable source commit `2f8ba78c6fc329ff2dc577a68c7b568b9f63f1c0`
**Nature:** Prospectively specified **read-only audit of earlier frozen reports**. NOT a new source IFC probe, IFC writer, author score, LLM experiment, protocol amendment or causal representation claim.

## Research question and frozen evidence

The independent variable remains **LLM-editable source representation**: declarative complete XML state editing (D) versus imperative Python/IfcOpenShell (I). The dependent measure is independently graded **actual model-produced** IFC output under equivalent task-relevant source facts, IFC editing capability and feedback constraints.

Historical D0/I0 outputs were deterministic, developer-written **nonblinded positive witnesses**, not independently sampled LLM runs. Selected native IFC byte equality on a task is not equivalent to full native source-information equality or complete write-capability equality.

The auditor reads SHA-256-pinned **v0.20** original45 protocol ledger, **v0.22** actual original source-role/schema census, **v0.30** evidence reconciliation, plus the six v0.23–v0.29 frozen original-public-task D0/I0 reports. Every one of the nine JSON report streams is verified against its byte-level SHA-256. It then **independently recomputes v0.30** from v0.20, v0.22 and the six selected original-task reports and refuses a mismatch. The source/question SHA, original category, CRUD, IFC schema, original source IfcProduct counts, safe typed XML count and public operation-family label are cross-checked per task against v0.20.

This process does **not** rescan 31 raw IFCs or reexecute prior developer native edits in v0.31; the actual source verification belongs to the explicitly cited frozen v0.22 worker and six older reports. Its substantive contribution is the first fail-closed **intersection of documented necessary source conditions and independently reconciled developer witnesses**, with an exhaustive all45 prioritized diagnostic queue rather than an eligible model trial subset.

## Original 45 — mutually exclusive diagnostic strata

| Diagnostic priority | Tasks | Meaning and next audit |
| --- | ---: | --- |
| P0 — current XML session rejects original IFC edition | **3** | `geometry_test_03`, `geometry_test_04`, `geometry_test_05`; the v0.22 implementation rejects IFC2X3/IFC4. Verify any schema extension using the untouched original inputs. |
| P1 — public named source product omitted from editable XML | **2** | `topological_test_01`, `topological_test_20`; independently verify task target visibility before write studies. |
| P2 — other task-required source role omitted | **7** | Frozen coarse required-role class census finds missing editable original products. This tier includes **three** previously byte-equal developer witnesses. Do not call these tasks impossible. |
| P3 — coarse checks pass and nonblinded developer witness exists | **8** | Selected real native D0/I0 byte equality; still needs full task-relevant facts/capabilities, independent scorer calibration and fair sealed model host. |
| P4 — coarse checks pass but no paired developer witness | **25** | Task-specific native write feasibility remains **unknown**, not failure. Candidate **for further offline feasibility audit**, not for matched paid trials. |
| **Total original intention-to-test** | **45** | Immutable task population; no deletion or reweighting by developer success. |

The **33** cases in P3+P4 pass **coarse necessary** role, named-public-reference and current schema/unit admission checks. Neither their task-specific geometry/topology/material/relationship facts nor native write equivalence has been proven. The tool reports **0/45 full task-relevant source information parity**, **0/45 full task-relevant native write capability parity**, **0/45 eligible matched causal model trials**, and **0 actual matched D/I LLM trials**.

The 9 original tasks with missing required role source objects comprise P1+P2. The 2 public GUID omissions are a *subset* of those nine; never add them. The 3 schema input rejections are disjoint from the nine. A shared limited read-only transcript was shown equal for all 45 previously, but cannot replace the missing full semantic/source/write equivalence proof.

## New inferentially important overlap and selection risk

Exactly **three** original tasks have historical **full native IFC D0/I0 byte-identical developer outputs** while the original public task's *required source role class* is not entirely exposed in the earlier editable typed XML:

- `geometry_test_18`: required original `Window` role incomplete; original author references/source mismatch means no valid original numeric author score.
- `geometry_test_19`: same `Window` role gap and scorer/source mismatch.
- `test_20`: original `Space` role incomplete; original author-callable developer pair at 0.5.

This is **not a contradiction**: a selected developer edit may operate on a smaller relevant subset of original objects, use alternate source facts or exploit special knowledge. A positive witness does not certify complete original role coverage, unbiased generalizability, or counterfactual LLM source equality. Conversely, the presence of extra native products does not prove the selected task cannot be solved via XML. Only task-specific independent source coverage and writer probes can resolve this.

The **11 total** native-paired developer witnesses are disproportionately concentrated in **delete (7) and update (4) tasks, with create (0)**. Although the original denominator is **15 create + 15 update + 15 delete**, the successful developer controls are not a representative task sample. Reporting model performance on these 11 as original45 benchmark performance would bias the study. The 9 callable developer author-score pairs and 2 mismatch cases are kept distinct; numerical author scores are not model performance.

## Launch and preregistration guard

All 45 rows retain `eligible_for_matched_causal_LLM_trial: false` and `actual_matched_LLM_outcome: NOT_RUN`. Priority tiers are diagnostic action buckets, **not** a performance-optimized sample inclusion rule. A separate *prospectively frozen*, task-specific criterion must be satisfied **before** enrollment: source-only task-relevant object/attribute/relationship/geometry availability in both representations, matched executable native edit capabilities, equal model-visible source/feedback budget, independently verified terminal submission isolation, and scorer/reference consistency. Preserve unsupported/failed/unknown classifications and the original45 ITT denominator; do not silently substitute a 33- or 11-case benchmark.

If the as-built systems have unequal source/write capabilities, the permitted research characterization is a **descriptive system comparison**, not a pure declarative-vs-imperative representation causal estimate. Original scorer mismatches need independent adjudication or author clarification rather than patching frozen grader/GT. Paid inference requires explicit model/provider and USD ceiling approval, and a separate reproducible execution-security review.

## Offline reproduction (no data/model/network/Docker required)

In the isolated v0.31 worktree with Python 3.12+ installed, run:

```powershell
python -m tools.audit_bibimbap_v031_eligibility
python -m tools.audit_bibimbap_v031_eligibility --check reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json
python -m unittest -q tests.test_bibimbap_v031_eligibility
```

SHA-256 of the committed, deterministic report:

`d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd`

`--check` compares the exact bytes without touching historical evidence. `--write` is write-once and fails on an existing destination. No question text, native source/target GUID, hidden ground truth, raw IFC, credentials, raw scorer code or model responses are exported. The audit detects missing/duplicate ID, SHA drift, cross-report public question/source mismatch, role count drift, unsafe parity promotion, altered frozen report or illicit LLM-score claims.

The pinned v0.30 replay and v0.31 overlap analysis constitute **secondary derived evidence**. As with any pinned predecessor reports, a previously undetected substantive error in a frozen worker is not disproven merely by reproducing that worker's JSON output. Current original-source and Docker availability are distinct readiness issues.

## Follow-on work priorities

1. **P0/P1/P2:** conduct read-only inspection of the exact original affected IFC sources and XML/API schemas, followed only by separately scoped safe positive/negative native **writer** probes; never silently mutate source IFC or change frozen author scorer.
2. **P4:** prior to any task inclusion, build independent native output/oracle witnesses for untested operations, particularly the **15 original create tasks**, rather than expanding only the already successful selected cases.
3. **P3:** independently audit each prior D0/I0 witness for full task-relevant source/relationship/geometry equivalence and shared executable write access. Preserve nonblinded selection provenance.
4. Verify actual Docker/terminal model host lifecycle **nondestructively**, including no result feedback leaks. No Docker reset, dataset download or paid model call is authorized by v0.31.

Original frozen files, benchmark identities, and all existing PRs remain untouched. Stack this change as a **Draft PR** against the v0.30 branch, not `main`.

## 2026-11-17 Windows host — separate nondestructive Docker status

At the time of this checkpoint, `docker --version` reported Docker CLI 28.3.2. A read-only `docker version --format '{{.Server.Version}}'` exited **1** because the selected `desktop-linux` context's `//./pipe/dockerDesktopLinuxEngine` endpoint was absent. `Get-Service com.docker.service` reported **Stopped / Manual**; no Docker-named processes were found and `wsl --list --verbose` showed `docker-desktop` and the other enumerated distributions **Stopped**. These observations indicate **this host has no currently available Docker Linux engine**, not an IFC semantic/parity failure; historical sealed Linux evidence is not reclassified as never having run. The isolated Python venv is available for selected non-Docker regression tests. No daemon, Windows service, WSL distribution or Docker Desktop process was started, restarted, reset or modified. A fresh secured Python worker/model-host execution remains blocked pending nondestructive, explicit environment recovery and independent sandbox review.
