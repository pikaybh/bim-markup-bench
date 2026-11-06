# BIM-Edit 36-task expanded pilot — preparation status

**Status: NOT RUN. Do not interpret this file as an experiment result or claim API-key validity.**

## What is prepared

- Public BIM-Edit task manifest: 324 tasks pinned to HF commit `2dc6462bfab145ddf81b43e9954322855b8443dc`; local ignored `data/tasks.jsonl`; SHA-256 `9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83`.
- Candidate subset: 36 tasks (2 chosen by deterministic SHA-256 ordering from each of 18 operation × category × scene cells). No model results examined. Six IFC entity classes represented, but not equally weighted; see manifest class counts.
- Two arms per task: direct editing of **declarative XML document state** vs LLM-generated Python/IfcOpenShell; 72 arm-trials for one repetition. This is **not** 72 API calls if multiple tool/feedback turns are needed.
- Local virtualenv on the Mac, with Python 3.9.6, IfcOpenShell 0.8.4.post1, OpenAI 2.48.0, python-dotenv 1.2.1, as of preparation. These are preliminary environment versions, **not yet the cross-platform validated G0 lockfile**.
- `.env` configured with an `OPENAI_API_KEY` variable but **neither its value nor validity is printed/stored in Git**. No API request was sent.
- Proposed model: `gpt-6-luna`. Cost planning only: 20,000 input + 5,000 output tokens per arm-trial, 72 trials, conservative rates $0.10/$0.50 per million tokens: approximately **$0.324**, excluding retries, external tools and actual variable input length. Proposed cap $5, **not yet explicitly approved in config**.

## Verification

```bash
cd /Users/pikaybh/Projects/bim-markup-bench
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/prepare_pilot_candidate.py
.venv/bin/python tools/pilot_preflight.py
```

The preflight must exit **2 / BLOCKED** until all G0/G1/G2 and scientific preregistration requirements have actual audited artifacts. Missing evidence must never be faked by editing status files.

## Blocking dependencies before any paid run

1. G0: #3 BIM-Edit input and GT IFC files checked, pinned, rights checked; #4 official/independent scorer audited; #8 GT and secret isolation. Note the model corpus is multi-GB and was **not downloaded** in preparation.
2. G1: #9–#16 implement actual XML source grammar, IFC projection/semantic diff, real geometry and topology edits, and deterministic D0/I0 oracle comparisons. A code snippet that merely calls IFC APIs is **not** a valid direct-markup model method.
3. G2: #17–#22 implement both LLM execution arms, sandbox, runner/budget control, blinded independent scorer and calibration.
4. G3: #23 freeze pilot manifest and protocol **after** capability audit, preserving ITT coverage. Record owner-approved model ID, budget cap and API permission. #24 executes actual paired trial; #25 analyzes data.

## Notes on reproducibility and API keys

Never commit `.env` or place the key in README, GitHub issues/PRs, logs or LLM prompts. The preflight only checks for a nonempty variable and does not authenticate against OpenAI. The code in this branch contains no live LLM invocation; a manual API call by another script would not be protected by this proposed cost cap. Use only an audited runner with a hard request/token budget and an isolated API key/project.

This repository and branch do not modify BIXML, Xim, Revit reverse-engineering worktrees or any production servers.
