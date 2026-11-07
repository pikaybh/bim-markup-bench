# G0 — Reproducible Development Environment

**Issue #7.** These offline checks do NOT implement a benchmark, XML runtime, independent evaluator or LLM API runner.

## Versions

- macOS ARM64 tested. Python 3.12.13 (pinned minor 3.12 in .python-version).
- uv version 0.8.5 used to generate uv.lock.
- IfcOpenShell 0.8.4.post1, OpenAI SDK 2.48.0, python-dotenv 1.2.1, jsonschema 4.25.1, PyYAML 6.0.3. Transitive dependencies and checksums in uv.lock.
- Other OS/arch combinations NOT validated; record wheel/kernel differences before claiming support.

## Fresh clone command sequence

1. git clone https://github.com/pikaybh/bim-markup-bench.git
2. cd bim-markup-bench
3. Install trusted uv 0.8.5.
4. uv python install 3.12
5. uv sync --frozen --python 3.12
6. .venv/bin/python tools/doctor.py --json
7. .venv/bin/python -m unittest discover -s tests -v
8. .venv/bin/python tools/cost_budget.py

The offline doctor checks Python and installed versions and writes/reopens a tiny SYNTHETIC IFC4 project in a disposable temporary directory. It never reads .env, real benchmark IFC or OpenAI API. Success code 0 = foundational smoke PASS; code 2 = FAIL. This does NOT demonstrate IFC Geometry or topology correctness.

## API credentials and rights

Copy .env.example to local .env, restrict permissions with chmod 600 .env and edit locally. Git ignores .env. No G0 script loads the key. The future model runner must use a trusted broker, never expose credentials to the LLM-generated Python process, logs or GitHub. Large licensed IFC corpora require separate download/storage permission and must remain outside Git.

## Reproducibility

Updating Python minor, IfcOpenShell, OpenAI SDK or lockfile requires a new reviewed PR and fresh smoke/tests. Pin exact platform, version, input hash and geometry-kernel details in each trial manifest; lockfile alone is insufficient for geometric reproducibility. No GitHub Actions or production infrastructure are involved.
