# Issue #97 — P1 retrospective error attribution and prospective case readiness

Date: 2026-11-12 KST. **P1 preparation only. No additional provider calls or costs.**

## P0 is immutable

The genuine P0 experiment was one real model-generated matched task (D/XML PASS, I/Python FAIL), with two calls to gpt-5.4-mini-2026-03-17 and a usage-based estimate of **$0.0072990**. Its native judgment, model-generated text hashes, original OWN IFC and selected source are unchanged. See reports/p0_first_real_llm_pair_evidence_20261112.json, SHA256 647bd2c7b170e5ffe506d4d9df2cd3206c8ac390701cf3b4957e2b7f6bbb366b. This remains an exploratory *OWN synthetic* task, never an official BIM-Edit score.

The I/Python model used Python built-in getattr and hasattr, both forbidden by the **P0** AST source policy, and therefore failed before native IFC output. The generated script also attempted to edit a nonexistent IfcWall.Height attribute. The actual source wall instead has an IfcExtrudedAreaSolid with Depth=3.0. This distinguishes **interface preflight failure** from an additional **model semantic error**: static acceptance alone would not make the code a correct IFC edit. A post-hoc sandbox grader timed out and provides no additional native score; do not upgrade P0.

## Prospective P1 policy, not retroactive scoring

A new, versioned static rule permits *only* direct read-only calls to getattr/hasattr with a literal, preapproved IFC attribute name. Dynamic attributes, dunder introspection, setattr/delattr, unsafe imports, secrets and OS/network constructs remain blocked. The parser still **does not execute** Python. The OS-isolated Linux Docker container remains mandatory.

The original P0 model-generated Python, whose SHA is verified before analysis, now passes this proposed static policy; its nonexistent Height attribute remains invalid. **Never recode the first I attempt as a success.** Tests cover accepted literal IFC property names and rejected introspection escapes.

For future P1 trials, the exact model-visible prompt/schema, the I-arm IfcOpenShell API notes (an extra affordance), the policy version and the one-shot budget must be frozen prospectively *before* observing new model results. Similar information access is a scientific constraint; matching token limits alone is not matching information.

## P1 next three owned task candidates — immutable original source

Original synthetic IFC: tests/fixtures/synthetic/input.ifc; SHA256
10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.
All instructions below use this OWN model, not the third-party BIM-Edit dataset.

| Frozen candidate | Required action | Current independent D0/I0 ceiling | Status |
| --- | --- | --- | --- |
| OWN-P1-WINDOW-MOVE-001 | Move the North Window and hosted Opening +0.5 m along wall local X, preserve everything else | move_hosted_opening: native parity PASS | D0/I0 supported ONLY; live isolated scorer pending |
| OWN-P1-WALL-CREATE-002 | Add straight Wall (0,5,0) to (4,5,0), height 3.0 m, thickness 0.2 m, Level 1; preserve others | create_standalone_wall: native parity PASS | D0/I0 supported ONLY; live isolated scorer pending |
| OWN-P1-DOOR-DELETE-003 | Remove Entrance Door and hosted Opening, close void, preserve unrelated IFC objects/relations | OWN model lacks required inverse relations for current scoped native Door deletion; compiler refuses without output | **BLOCKED** — no LLM trial until resolved |

Door detail: this source Door has only IfcRelFillsElement and
IfcRelContainedInSpatialStructure inverses; the exact scoped deletion
implementation requires one SpaceBoundary, material/classification,
two Psets and a type relationship in addition to the above. Direct
XML deletion of Door+Opening was **tested** and failed closed with
CompilerError. Do not quietly swap in Window deletion or redefine the
denominator after viewing scores.

The already existing tools.verify_g1_oracles audit was rerun:
6 deterministic unit tests passed; 4 developer-written synthetic
D0/I0 IFC outputs verified. This proves **engine ceiling only**.
Evidence: reports/p1_g1_own_ceiling_20261112.json,
SHA256 0c96351f066b85e7642a45537a7fdaa9306bf6c5fb0efdcc2e9b3d23ad4a904e.
Offline attribution and eligibility:
reports/p1_offline_attribution_eligibility_20261112.json,
SHA256 32ee58d46989d7c72771190a4a758c7f7e548184f503c9118977a99ddff2837d.

## Next actions, in priority order

1. First extend the verified OWN-only Docker candidate execution and independent grader beyond the P0 wall-height task for the two D0/I0-passing cases. Current worker/grader is still fixed to wall height 3.3 m; therefore **0 P1 tasks are ready for paid live model scoring**. Keep failures separate from valid model failures. Then assess the **OWN source fixture vs scoped Door deletion** incompatibility
   without widening required features just to obtain a passing model score.
   If a new synthetic Door input is necessary, version/freeze it separately
   and independently prove D0/I0 operation before LLM inference.
2. Freeze full prospective P1 trial contract: same model and public IFC
   observation, explicit arm-specific API reference, updated safety policy,
   one attempt each, protected answer, independent IFC success and model/
   engine failure categories.
3. Only then seek **separate new approval** for additional P1 paid LLM
   calls. The previous $1 limit was specific to **two P0 calls** and is
   NOT ongoing permission for the additional 3x2 P1 trial.

**Verified P1 at present: 2 D0/I0-only eligible native cases; 1 blocked; 0 P1 live worker-ready cases; 0 additional
model calls; $0 additional API cost; official benchmark scores 0.**
