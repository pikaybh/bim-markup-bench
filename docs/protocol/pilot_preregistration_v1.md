# BIM-Edit paired pilot v1 — DRAFT, NOT preregistered

**Status: candidate only. No scored trial, approved model, payment, or scientific freeze.**

## Research question

H1 (primary): With identical source IFC, task instruction, model and
computational budgets, does direct LLM editing of declarative BIM markup
source yield a higher strict IFC edit success rate than LLM-generated
Python/IfcOpenShell authoring?

The direct condition edits building.xml source text through file editing
only. It NEVER receives a BIM authoring CommandBus or geometry mutation API.
A separate trusted compiler transforms valid markup to native IFC.
The imperative condition generates solution.py and must execute only within
an independently verified sandbox. A third independent grader consumes
the original input IFC, hidden GT IFC and result IFC without any arm label.

H2 (secondary): Differences in three independently measured IFC axes,
Geometry, Semantics and Topology, plus invalid, blocked and unscorable
outcome rates. H3 (secondary): Paired latency, actual model token usage,
actual billed cost, unwanted model changes and authoring/tool violations.

## Population and sampling

Primary 36-task candidate IDs live in manifests/pilot_36_candidate_v0.json.
Public 324-row metadata is pinned to Hugging Face task revision
2dc6462bfab145ddf81b43e9954322855b8443dc,
SHA256 9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83.

Exactly two IDs from each of 18 cells: 3 create/update/delete operations
× 3 direct/spatial/topological instruction classes × 2 artificial/realistic
scenes. In each cell sort records by SHA256 of the string
BIM-Edit-pilot-v0-2026-11-07|task_id, breaking ties by task ID; take
the first two. No model outcomes or hidden IFC ground truths influenced
this candidate selection. All six IFC classes happen to be represented,
but class frequencies are not balanced.

All 36 tasks are assigned to both arms: 72 trial slots per repetition.
Planned scheduler repetition seed is 11, deterministic arm-order shuffle
seed is 1234. These are runner randomization seeds, not provider model
sampling seeds. Initial candidate uses one repetition.

Do NOT filter the 36 cases after observing pilot results. The primary
intention-to-treat denominator includes every assigned task even if the
implementation is unsupported, no output is produced, or a run crashes.
A separately declared common-supported subset must be determined before
observing model scores, based on documented D0/I0 engine capabilities
and source/GT IFC audit. A replacement task selection needs a new
protocol revision, reason and prospectively frozen ID list.

## Conditions and fairness

Both arms must use the same verified provider model snapshot and sampling
configuration, identical original IFC bytes and natural-language task,
the same semantic model observation, total tool-turn/token/time limits
and predeclared feedback policy. The authoring method references
necessarily differ (XML syntax versus general Python/IfcOpenShell API
reference); this distinction is recorded rather than concealed.

Draft: one-shot, one attempt per arm/task, max 180 seconds, max 20,000
input + 6,000 output tokens per attempt, concurrency 1. No feedback
loop may be added after seeing results. Provider, exact model/snapshot,
temperature, seed support, price quote and charged token accounting
remain UNSELECTED / UNVERIFIED. Existing historical pricing and model
placeholders were not verified and are intentionally removed.

The USD 5 project cap is PROPOSED, not explicitly approved. Do not
perform any paid call before explicit owner approval and independently
audited hard budget enforcement.

## Endpoint definitions and failures

Primary per-task strict pass: each independent IFC Geometry, Semantics
and Topology score >=0.98 AND zero unwanted collateral mutations.
The current scorer origin is independent-reimplementation,
independent-ifc-three-axis-v0.1, and is NOT official BIM-Edit equivalent.
Do not report paper-headline scores as comparable.

Failure/invalid cases remain in ITT: malformed candidate IFC gets
explicit strict failure and 0/0/0 under the frozen independent rule.
Source IFC / GT IFC invalidity, missing verified reference geometry
or unresolved eligibility yields BLOCKED/UNSCORABLE with null numeric
axes and strict failure. Do not silently drop or replace them. Report
these separately rather than misrepresenting undefined scores as 0.
Time limit, budget denial, tool policy violation or no output also
count as strict failures with separately labeled reasons.

## Statistics

The pilot's principal descriptive effect is the mean of 36 paired
strict-pass differences (direct XML minus Python, each in -1, 0, +1).
Provide both numerator/denominator and a 95% confidence interval if
there are enough independent source IFC clusters. The planned
cluster bootstrap retains both arm outcomes within each task,
resamples original input IFC groups 10,000 times, and gives percentile
intervals; clusters must be audited from actual original IFC paths.
Do not treat multiple tasks derived from one IFC as independent.
A paired exact McNemar discordance count/test is descriptive.
For three secondary axis outcomes use Holm multiplicity correction.
Latency, tokens and cost are exploratory/descriptive.
A 36-task feasibility pilot is not a powered confirmatory full
324-task benchmark; no numeric power claim is justified before
the true source-file clustering and attainable outcomes are audited.

## Safe execution and protocol freeze

The present macOS Docker daemon is not running/verified. Same-user
directories and static Python checks are NOT kernel/VM isolation.
Generated Python must never execute before a restricted nonroot worker,
network/file/GT protection, secret-stripped environment and CPU/memory/
wall-time/output quotas pass independent negative tests. The provider
key is held by the trusted request broker, not inside candidate scripts.
The model gets no hidden ground truth or grader target GUIDs.

A true prospective freeze requires immutable commit SHA, task ID list
and data hash, official IFC/GT content audit, independent calibrated
score provenance, D0/I0 capability matrix, signed security gate,
reviewer, model/version/pricing, maximum budget approval and UTC
freeze timestamp, all recorded BEFORE model output inspection.
Missing conditions MUST prevent live execution. Changes after
scored results exist require a new frozen protocol and an append-only
deviation entry; post-hoc analyses are explicitly exploratory.

This document is not a signoff. The automatic pilot preflight
always returns blocked until independent evidence and approval.
Production BIXML/Xim is not part of this study.
