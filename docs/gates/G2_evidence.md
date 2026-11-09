# Gate G2 — evidence, remaining blockers, no live Pilot authorization

Current state: **BLOCKED_FOR_LIVE_MODEL_PILOT (NO)**.

The protocol's main distinguishing mechanism is LLM direct editing of
declarative BIM markup source, not invoking a typed BIM authoring API.
Our toy source-only interface and Python imperative comparison envelope
exist, but neither has executed a real scored, matched LLM trial.

## Evidence available

- G1 #16: Six independently hand-authored synthetic D0 XML-vs-I0 Python
  IFC editing cases with native IFC geometry/semantic/topology parity.
- G2 #17: Declarative building.xml text edit stub, trusted isolated
  compiler invocation only outside the model-visible API; file tooling
  rejects Python authoring commands.
- G2 #18: Python control source-only submission and static AST policy,
  unconditionally refusing candidate execution.
- G2 #19: Independent task/arm file-layout staging, original input hashes,
  model-view GT field filter. NOT OS security isolation because both
  compartments still share the same host user identity.
- G2 #20: Eight deterministic zero-billing mock trial manifests with
  two tasks × two arms × two seeds. The original model contexts agree and
  are byte-hash tracked; resumptions reject changed source, prompt,
  budget and artifact bytes. No model output or IFC editing occurred.
- G2 #21–#22: Independent, nonofficial, native IFC scorer; 17/17 own
  synthetic calibration assertions pass, including 14 seeded violations,
  unit mismatch, mesh/placement/relationship errors and model-blindness.
  Full measurement uses real native IFC files, never XML text alone.

## Release blockers (all must be addressed before G3)

- Full licensed official benchmark source/GT IFC byte and relationship audit
  for all 324 task records has NOT been completed.
- Official scoring implementation is not publicly released. The current
  independent scorer has not been calibrated against official GT tasks.
- Complete D0/I0 six-class CRUD and complex host/space geometry, matched
  tool/observation parity and ground-truth firewall have not been
  independently proven on the official corpus.
- Real OS/container network, process, file mount, secret isolation and
  resource limits are NOT verified; generated Python cannot be executed.
- Durable real model provider execution, tokens/cost accounting, retries,
  matching budget and explicit paid-run authorization are NOT implemented.
- No prospective scored primary benchmark trial and no official task
  success results exist. This gate cannot be bypassed with a command flag.

## Machine-verifiable commands

    .venv/bin/python -m tools.calibrate_g2
    .venv/bin/python -m tools.calibrate_g2 --enforce
    .venv/bin/python -m unittest discover -s tests -v

The enforced gate must return code 2. The independent report and 108-row
capability ledger are saved under reports/, excluding raw prompt/GT paths
or target GUIDs. This is an engineering preflight, not a positive trial.

Do not launch live model calls on the strength of these local tests.
No Xim/BIXML production engine or user server endpoint was modified.


## Follow-up, 2026-11-09: independent blind public IFC scorer (partial)

The G2 #19 Linux AMD64 OWN synthetic candidate/GT compartment proof
has now been extended with a separate G2 #21 pinned public IFC grader
self-check. A dedicated OCI image contains only the independent IFC
scorer, not an authoring agent. Three already-hash-audited public
reference tasks produce the expected perfect GT-vs-GT axis scores;
unmodified and invalid outputs fail. All four grader mounts are
read-only; the host checks prestart Docker HostConfig, blocks injected
secret/env/arm/tool mounts, and sanitizes metric outputs. Unlike the
original G2 evidence above, real Linux namespace isolation of this
limited grader has now been executed on Windows. However there
is still no independently verified OFFICIAL scorer implementation,
full GT licensing/corpus audit, live agent/model trial or formal
calibration. The global gate remains BLOCKED_FOR_LIVE_MODEL_PILOT.
Details: docs/gates/G2_blind_public_scorer_evidence.md.

### Regression result for blind scorer extension

Windows (pinned Linux AMD64 scorer + OWN candidate images) full suite:
316 tests; 309 passed, 7 platform/dependency skips, 0 failed.
Primary paid-pilot preflight returned code 2 (BLOCKED).
No official benchmark model scores or API calls were produced.
