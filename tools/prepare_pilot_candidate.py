#!/usr/bin/env python3
"""Deterministic, data-pinned 36-task *candidate* sampler for BIM-Edit.

This DOES NOT run any LLM, model, IFC engine, or grader. This file intentionally
writes only public task IDs & strata, not ground-truth paths/target GUIDs.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

DATA_REVISION = '2dc6462bfab145ddf81b43e9954322855b8443dc'
DATA_SHA256 = '9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83'
SEED = 'BIM-Edit-pilot-v0-2026-11-07'
EXPECTED_OPS = {'create', 'update', 'delete'}
EXPECTED_CATS = {'direct', 'spatial', 'topological'}
EXPECTED_SCENES = {'scene:A', 'scene:R'}
EXPECTED_CLASSES = {'IfcWall','IfcSlab','IfcSpace','IfcDoor','IfcWindow','IfcColumn'}


def select(data_file):
    raw = data_file.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != DATA_SHA256:
        raise ValueError('Frozen task data hash mismatch: '+actual)
    records = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    if len(records) != 324:
        raise ValueError('Expected 324 tasks, got '+str(len(records)))
    ids = [r['task_id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate task_id')
    strata = collections.defaultdict(list)
    for r in records:
        tag = [x for x in r.get('tags',[]) if x in EXPECTED_SCENES]
        if len(tag) != 1 or r['operation'] not in EXPECTED_OPS or r['category'] not in EXPECTED_CATS:
            raise ValueError('unexpected task metadata: '+r['task_id'])
        k=(r['operation'], r['category'], tag[0])
        strata[k].append(r)
    if len(strata) != 18:
        raise ValueError('Expected 18 nonempty strata, got '+str(len(strata)))
    sample=[]
    for k in sorted(strata):
        pool=strata[k]
        if len(pool) < 2:
            raise ValueError('too few examples for '+repr(k))
        pool = sorted(pool,key=lambda r: (hashlib.sha256((SEED+'|'+r['task_id']).encode()).hexdigest(),r['task_id']))
        for record in pool[:2]:
            sample.append({'task_id':record['task_id'], 'operation':k[0], 'category':k[1], 'scene':k[2], 'entity_type':record['target']['entity_type']})
    if len(sample) != 36:
        raise AssertionError('Sample size error')
    counts=collections.Counter(r['entity_type'] for r in sample)
    if set(counts) != EXPECTED_CLASSES:
        raise ValueError('Unrepresented IFC type, choose and document a different predeclared seed: '+repr(dict(counts)))
    return {
      'status':'CANDIDATE_NOT_PREREGISTERED',
      'warning':'DO NOT RUN LLMs OR CLAIM PILOT RESULTS. G0/G1/G2 ORACLES AND COST APPROVAL REQUIRED.',
      'benchmark':'BIM-Edit',
      'task_source':'https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks',
      'task_revision':DATA_REVISION,
      'task_data_sha256':DATA_SHA256,
      'sampling_algorithm':'2 tasks per (operation,category,scene) stratum; SHA256(seed|task_id), lowest 2 lexically',
      'seed':SEED,
      'sample_size':36,
      'runs_per_repetition':72,
      'expected_arms':['direct_declarative_xml','imperative_python_ifcopenshell'],
      'class_counts':dict(sorted(counts.items())),
      'tasks':sample,
      'gate_status':{'G0':'NOT_PASSED','G1':'NOT_PASSED','G2':'NOT_PASSED','BUDGET':'NOT_APPROVED'},
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=Path('data/tasks.jsonl'))
    parser.add_argument('--out',type=Path,default=Path('manifests/pilot_36_candidate_v0.json'))
    a=parser.parse_args()
    data=select(a.data)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('candidate only',data['sample_size'],'tasks,',data['runs_per_repetition'],'arm executions')
    print('entity type distribution:', data['class_counts'])
    print('manifest:',str(a.out))

if __name__=='__main__': main()
