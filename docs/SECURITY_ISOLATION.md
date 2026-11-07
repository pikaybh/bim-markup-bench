# G2 #19 — Isolated-task file layout (partial)

**Result: file layout PASS; OS container isolation NOT VERIFIED.**
The repository does not permit generated Python execution or paid
model trials under the present security configuration.

The trusted controller creates three distinct per-task directories:
agent_workspace, trusted_compiler and grader. The run name is derived
from the task ID, experiment arm, seed and immutable IFC checksum. A
duplicate run root is rejected. Both experiment arms receive the exact
same source IFC content hash and independently copied original source.
Only the trusted compiler receives the private manifest. The grader
directory is not part of any model-visible bundle.

Task-visible data is restricted to task instruction, XML projection,
language reference, source hash and source filename. Target annotations,
hidden reference files, grading data and credentials are not included.
The verifier checks the declared filename inventory, disallows symlinks
and unexpected files, and confirms original IFC checksums.

**Security limitation:** These directories run under the same host user.
UNIX file permissions and textual policies alone cannot enforce
process isolation. The physical container engine was unavailable during
this run, so network, subprocess, filesystem namespace and worker
environment separation have not been independently demonstrated.
The generated-code entrypoint remains unconditionally blocked.

Remaining acceptance criteria before G2 #19 can close: independently
tested restricted worker environment, separate filesystem boundaries,
restricted runtime permissions, no host secrets in worker environment,
fixed memory/CPU/time/output quotas and validation of all negative
security scenarios inside that worker. Until then, G1's official task
gate and paid-experiment gate remain blocked.

To reproduce the safe offline unit checks:

    uv sync --frozen --python 3.12
    .venv/bin/python -m unittest tests.security.test_sandbox -v

The tests stage only our own small IFC fixtures in ephemeral scratch
directories. No generated candidate code or paid model calls occur.
