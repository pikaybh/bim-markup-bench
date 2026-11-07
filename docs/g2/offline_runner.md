# G2 #20 — reproducible offline paired-run scheduler (partial)

**Status:** the local mock scheduler and record/defense tests are implemented.
**Live LLM benchmark not ready**: these are scheduled placeholder responses,
NOT generated solutions, scored BIM-Edit runs or independent IFC evaluation.

## How to reproduce without API credentials

All commands are run from the repository root. They do not call model
providers or execute generated Python.

    uv sync --frozen --python 3.12
    .venv/bin/python -m src.runner.cli doctor
    .venv/bin/python -m src.runner.cli validate-data
    mkdir -p /tmp/bim-g2-offline-demo
    .venv/bin/python -m src.runner.cli run --offline-mock \
       --task-list tests/fixtures/offline_two_tasks.json \
       --input-ifc tests/fixtures/synthetic/input.ifc \
       --arm both --model offline/mock-v0 --seeds 11,29 \
       --shuffle-seed 1234 \
       --budget configs/experiment.sample.yaml \
       --output-root /tmp/bim-g2-offline-demo
    .venv/bin/python -m src.runner.cli report \
       --output-root /tmp/bim-g2-offline-demo
    .venv/bin/python -m src.runner.cli run --offline-mock \
       --output-root /tmp/bim-g2-offline-demo --resume
    .venv/bin/python -m src.runner.cli score

A repository-local command wrapper is provided as bin/bench with the
same subcommands. Use the project Python virtual environment.

The score command **must exit 2**, reporting that the official independent
scorer is not ready. The doctor --enforce command also returns 2. Without
--offline-mock, the run command refuses to start. Only the fixed synthetic
IFC and own synthetic task envelopes are permitted, not the raw BIM-Edit
task record containing hidden GT/evaluation fields.

## What is actually exercised

Two synthetic task envelopes × two arms (direct_xml, imperative_python)
× two seeded repetitions create eight attempt manifests. Task/seed
pairs use a deterministic SHA-derived random shuffle of arm order,
so run order is reproducible across restarts. No external provider
is called. Both arms have exactly the same frozen observational
task instruction, source IFC hash and XML/model-language reference;
the system prompt hash differs by declared authoring method.

Each record has a schema-validated deterministic run ID including
experiment, task, arm, seed, attempt and source input digest. Records
store dataset revision, observed backend versions, model context
and system prompt hashes, artifact digests, budget caps,
mock raw response, source placeholder, compiler diagnostics
placeholder, stdout/stderr placeholders, output IFC SHA **null**,
metrics ref **null**, and explicit failure blockers. Every persisted
artifact gets an SHA-256, checked at report time and before resume.
There are no provider-reported token counts or charges; token counts
are explicitly labeled rough UTF-8-byte/4 **preflight estimates**,
not actual token usage. The mock emits no billable provider calls.

A repeated run refuses to overwrite existing trial artifacts.
--resume skips only intact records with identical original task
context, prompt, backend and budget policy. Changing registered
instruction, recorded output, budget, model, or IFC source rejects
resume. A new --attempt needs a correspondingly higher
predeclared attempt budget and does not modify prior records.

Mock token cap exhaustion and an injected synthetic clock timeout
produce explicit BLOCKED_TOKEN_BUDGET and BLOCKED_WALL_TIME manifests.
No claim is made that this can interrupt an actual external model
request or rogue Python process: that requires #19 isolation and
a durable billing broker.

## Security and scientific limitations

- The scheduler only records mock responses, and produces **no edited IFC**
  and **no scored result**. The G1 independent D0/I0 synthetic oracles
  remain separate from this G2 mock scheduler.
- No real provider adapter has been implemented or authorized. Seed support,
  streaming timeouts, billing, actual token counts and real provider
  retries must be implemented and verified later.
- Actual generated Python execution is disabled because the required OS
  sandbox could not be verified (#19).
- Full 324 official input/GT IFC content verification, independent
  scorer and six-class geometry coverage remain incomplete.
  The official G1 release gate continues to return BLOCKED.
- A mock report with eight entries is only an **orchestration fixture**,
  never an experimental success percentage.
- All files are in the standalone bim-markup-bench experiment repository.
  No Xim/BIXML or production server changes.

## Local tests

    .venv/bin/python -m unittest tests.test_runner -v
    .venv/bin/python -m unittest discover -s tests -v

Dedicated tests cover 8 records, paired arm order, context hash parity,
estimated-vs-reported costs, prompt/budget tamper rejection, GT/source
path blocking, immutable resume behavior, token/time cutoffs, no-live
gates and report SHA integrity. All demo output requires a caller-
selected scratch directory and is not committed to Git.
