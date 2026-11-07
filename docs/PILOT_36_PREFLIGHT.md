# BIM-Edit 36-task candidate — NOT RUN, NOT PREREGISTERED

The candidate uses Hugging Face BIM-Edit Tasks revision
2dc6462bfab145ddf81b43e9954322855b8443dc,
local public 324-row metadata SHA-256
9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83.

A deterministic hash sampler chose two IDs in each of 18 operation ×
instruction category × scene cells (36 unique tasks). All six IFC
classes appear, with deliberately unequal class counts:
Wall 12, Space 9, Window 6, Slab 5, Door 3, Column 1.
Two matched arms would create 72 arm-trial slots in one repetition.
The candidate is not yet a frozen/scorable sample: official source/GT
IFC content, rights and per-case D0/I0 feasibility remain unchecked.

The previous draft's purported current model ID and pricing quote were
not independently validated. The model/provider/snapshot/temperature,
provider seed support and latest price remain null/unselected.
USD 5 is a proposed, NOT approved spend cap. No API key is read
or checked by the pilot scripts; key presence alone proves neither
authorization nor a working model transport.

Reproduction from pinned Python 3.12 environment:

    .venv/bin/python tools/prepare_pilot_candidate.py
    .venv/bin/python -m tools.pilot_preflight
    .venv/bin/python -m unittest tests.test_pilot_candidate -v
    .venv/bin/python -m unittest tests.test_pilot_preflight -v

The preflight must return exit code 2 even when metadata ID/strata
integrity is valid: original 324 source and GT IFC files, kernel
isolation, official metric calibration, matched production code
execution and explicit paid budget approval are NOT verified.
Full draft design, analysis and missing-data rules:
docs/protocol/pilot_preregistration_v1.md.

Do NOT invent a frozen manifests/pilot_tasks_v1.json until full
physical source/GT audit, model selection and scientific signoff.
No paid model call, official benchmark scoring or production Xim/BIXML
modification is performed here.
