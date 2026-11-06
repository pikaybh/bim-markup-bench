#!/usr/bin/env python3
"""NON-BILLING readiness check. Never invokes an API or prints a key."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT/'configs/pilot_36_plan_v0.json').read_text())
    manifest = json.loads((ROOT/'manifests/pilot_36_candidate_v0.json').read_text())
    problems=[]
    env=ROOT/'.env'
    has_key=False
    if env.is_file():
        # Inspect names and only an in-process Boolean; never print the value.
        for line in env.read_text().splitlines():
            if line.startswith('OPENAI_API_KEY='):
                val=line.split('=',1)[1].strip()
                has_key=bool(val) and val not in ('sk-여기에_실제_API_KEY','sk-여기에_발급받은_API_KEY')
                break
    has_key=has_key or bool(os.getenv('OPENAI_API_KEY'))
    print('API_KEY_CONFIGURED:',has_key, '(validity NOT checked; no API request made)')
    if not has_key:
        problems.append('No API key configured')
    if manifest['status'] != 'FROZEN_PREREGISTERED':
        problems.append('Task manifest not preregistered; current status: '+manifest['status'])
    data=ROOT/'data/tasks.jsonl'
    if not data.exists():
        problems.append('Public tasks metadata not cached locally')
    elif hashlib.sha256(data.read_bytes()).hexdigest() != manifest['task_data_sha256']:
        problems.append('Task metadata checksum does not match frozen revision')
    else:
        print('PUBLIC_TASKS_SHA256: PASS')
    if len(manifest['tasks']) != 36 or manifest['runs_per_repetition'] != 72:
        problems.append('Invalid candidate 36 task / 72 arm run structure')
    if not config['max_total_usd_explicitly_authorized'] or not config['paid_calls_enabled']:
        problems.append('Paid API calls are disabled pending explicit budget approval and a working harness')
    missing=[g for g in config['hard_requirements'] if not (ROOT/'evidence/gates'/(g+'.json')).is_file()]
    if missing:
        problems.append('Missing independent evidence for gates: '+', '.join(missing))
    pr=config['price_estimate_only']
    n=len(manifest['tasks'])*len(config['arms'])*int(config['repetitions'])
    estimate=n*(pr['input_tokens_per_arm_task']*pr['input_usd_per_million']+pr['output_tokens_per_arm_task']*pr['output_usd_per_million'])/1_000_000
    print('TASKS:',len(manifest['tasks']),'MODEL_EXECUTIONS:',n)
    print('MODEL:',config['model'])
    print('PLAN_ONLY_COST_ESTIMATE_USD:',format(estimate,'.4f'))
    print('PROPOSED_COST_CAP_USD:',config['max_total_usd_proposed'])
    print('MODEL_RUNS_STARTED: 0')
    for p in problems:print('BLOCKED:',p)
    print('READINESS:', 'BLOCKED' if problems else 'GATES_PRESENT_REQUIRE_INDEPENDENT_REVIEW')
    return 2 if problems else 0

if __name__ == '__main__': sys.exit(main())
