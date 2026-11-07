import json
import unittest
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]

class CandidateTests(unittest.TestCase):
    def test_stratified_count(self):
        data=json.loads((ROOT/'manifests/pilot_36_candidate_v0.json').read_text())
        self.assertEqual(data['sample_size'],36)
        self.assertEqual(data['runs_per_repetition'],72)
        self.assertEqual(len(data['tasks']),36)
        self.assertEqual(len({r['task_id'] for r in data['tasks']}),36)
        groups=Counter((r['operation'],r['category'],r['scene']) for r in data['tasks'])
        self.assertEqual(len(groups),18)
        self.assertEqual(set(groups.values()),{2})
    def test_no_ground_truth_in_agent_manifest(self):
        data=json.loads((ROOT/'manifests/pilot_36_candidate_v0.json').read_text())
        for row in data['tasks']:
            self.assertEqual(set(row),{'task_id','operation','category','scene','entity_type'})
            self.assertNotIn('ground_truth_ifc',row)
            self.assertNotIn('target',row)
    def test_readiness_is_not_claimed(self):
        data=json.loads((ROOT/'manifests/pilot_36_candidate_v0.json').read_text())
        plan=json.loads((ROOT/'configs/pilot_36_plan_v0.json').read_text())
        self.assertEqual(data['status'],'CANDIDATE_NOT_PREREGISTERED')
        self.assertFalse(plan['paid_calls_enabled'])
        self.assertFalse(plan['maximum_total_spend_usd_explicitly_authorized'])

if __name__=='__main__':unittest.main()
