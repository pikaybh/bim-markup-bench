# P0 — GPT-6 Luna real paired IFC-edit replay (2026-11-12)

## Method / model-selection correction

The user-configured model in the ignored .env file was OPENAI_MODEL=gpt-6-luna.
The former GPT-5.4 mini result is real, but was run with the wrong model.
The replay uses the **exact earlier P0 code and original AST policy** at
f27e231e87b1006cc6b25be84c6aa06b664af4f1 in a separate detached
worktree, not the later P1 relaxed policy. Both D/I model-facing
prompts were checked against the prior saved packets and found to
be identical. OWN source IFC SHA256:
10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.

## Genuine two-call GPT-6 Luna results

Task: change North Wall height from 3.0m to 3.3m; preserve all others.

| Measurement | D (XML) | I (Python) |
| --- | --- | --- |
| Actual API model | gpt-6-luna | gpt-6-luna |
| Real calls | 1 | 1 |
| Input tokens | 2,336 | 2,602 |
| Output tokens | 719 | 1,536 |
| Usage-estimated USD | $0.0005931 | $0.0010282 |
| Original frozen P0 policy | PASS | FAIL (AST disallowed yield) |

**Total USD $0.0016213 estimated token usage** within user-approved
$1.00 cap. Two-call conservative upfront budget envelope $0.0058980.
Standard model pricing was verified at $0.10/M input and $0.50/M
output. Provider invoice not independently reconciled. No retries.

D/XML: actual model-generated XML compiled, native IFC independent
OWN checker passed. Result IFC SHA256:
c30fee1b2900ab0c8c3f17d846850acd189a717c1558689290cdb1e1fa4b5cdd.
The D text SHA was exactly the same as in the previous 5.4-mini test.

I/Python: Luna generated a valid-looking IfcOpenShell algorithm that
finds IfcExtrudedAreaSolid and sets Depth to 3.3. The original AST
policy rejected its recursive generator (yield construct) before
the normal P0 native execution stage. This remains the **original
strict failure**.

**Post-hoc independent execution (zero extra model calls):** the
unaltered I model code was run in the pinned OWN-only isolated Linux
container and a separate independent grader. Both the isolated
grader and a second independent native IFC checker passed. The
verified I native output SHA256:
0846754c5cc8b5b7c86c7b1bf0d33b4b5d48b7055dda5346e5c58106711c6cd9.
This **does not retroactively convert the original frozen P0
preflight result to PASS**. It does show that the Python output
could correctly modify native IFC under OS isolation.

## Research interpretation

One synthetic wall-height task and one generation per model/arm cannot
prove general XML superiority. P0 Python failures differed:
5.4 mini attempted a nonexistent direct IfcWall.Height, whereas
GPT-6 Luna correctly targeted physical sweep Depth but was rejected
by the original AST policy. The imperative arm has extra IfcOpenShell
API notes; this interface asymmetry must be disclosed. P1 must freeze
prospective changes to the Python policy and independent per-task
evaluators before any new model results. No official BIM-Edit scores.

## Audit, no private data in Git

Git-safe report:
reports/p0_gpt6_luna_real_pair_replay_20261112.json
SHA256 71cdab318c6031a1e1d660ba4bd679cbc478cb3d4820490ec2a6bb795e0b821e.

Ignored local raw XML/Python, private config and independently graded
IFC outputs:
../bim-markup-bench-p0-luna-replay/results/p0_gpt6_luna_replay_20261112_run01/

Do not commit the .env file, API credentials, hidden GT or raw model
outputs. Earlier 5.4/P1 reports, main and existing stash remain intact.
