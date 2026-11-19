"""BIM-Edit primary pilot source-path metadata-only audit regression tests."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_bim_edit_pilot_input_clusters import (
    PilotMetadataError, TASK_SHA256, _load_json_bytes,
    _path_only, build_pilot_source_path_audit, run_audit,
)


class TestPinnedPrimaryPilotSourceGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.tasks = (cls.root / "data/tasks.jsonl").read_bytes()
        cls.pilot = _load_json_bytes((cls.root / "manifests/pilot_36_candidate_v0.json").read_bytes())
        cls.tree = _load_json_bytes((cls.root / "data/bim_edit_remote_tree.json").read_bytes())
        cls.revision = _load_json_bytes((cls.root / "manifests/bim_edit_revision.json").read_bytes())
        cls.remote = _load_json_bytes((cls.root / "data/bim_edit_remote_audit.json").read_bytes())

    def create(self, *, pilot=None, tree=None, revision=None, remote=None, tasks=None):
        return build_pilot_source_path_audit(
            self.tasks if tasks is None else tasks,
            self.pilot if pilot is None else pilot,
            self.tree if tree is None else tree,
            self.revision if revision is None else revision,
            self.remote if remote is None else remote,
        )

    def test_pinned_task_sha(self):
        self.assertEqual(hashlib.sha256(self.tasks).hexdigest(), TASK_SHA256)

    def test_real_324_and_36_path_clusters(self):
        report = self.create()
        self.assertEqual(report["all_task_rows"], 324)
        self.assertEqual(report["all_unique_exact_input_paths"], 88)
        self.assertEqual(report["pilot_task_rows"], 36)
        self.assertEqual(report["pilot_unique_exact_input_paths"], 25)
        self.assertEqual(report["pilot_repeated_input_task_rows"], 11)
        self.assertEqual(report["largest_single_input_path_task_count"], 7)
        self.assertEqual(report["remote_total_metadata_bytes_of_distinct_pilot_inputs"], 777555298)
        self.assertTrue(all(g["content_hash_verified_from_downloaded_ifc"] is False for g in report["groups"]))
        self.assertNotIn("independently_verified_source_families", report)
        self.assertNotIn("independent_model_trial_ready", report)

    def test_existing_metadata_grouping_reproducible(self):
        self.assertEqual(run_audit(self.root), run_audit(self.root))
        report = self.create()
        self.assertEqual(len({g["path_group_key_sha256"] for g in report["groups"]}), 25)
        self.assertEqual(sum(g["task_count"] for g in report["groups"]), 36)

    def test_paths_are_source_only_not_gt_or_answers(self):
        report = json.dumps(self.create(), sort_keys=True)
        self.assertNotIn("ground_truth_ifc", report)
        self.assertNotIn("target_guid", report)
        self.assertNotIn("reference_ifc", report)
        self.assertNotIn('"prompt"', report)

    def test_noncanonical_path_rejected(self):
        for path in ("data/realistic/../secret.ifc", "data/realistic/a.ifc/secret",
                     "data/unknown/m.ifc", r"data\realistic\m.ifc", "data/artificial/no.step"):
            with self.subTest(path=path), self.assertRaises(PilotMetadataError):
                _path_only(path)

    def test_invalid_cohort_status_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["status"] = "PREREGISTERED"
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_invalid_cohort_revision_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["task_revision"] = "0" * 40
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_duplicates_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["tasks"][1] = copy.deepcopy(p["tasks"][0])
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_unlisted_task_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["tasks"][0]["task_id"] = "UNLISTED"
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_provenance_metadata_mismatch_rejected(self):
        rev = copy.deepcopy(self.revision)
        rev["model_revision"] = "bad"
        with self.assertRaises(PilotMetadataError):
            self.create(revision=rev)

    def test_source_file_removed_from_tree_rejected(self):
        tree = copy.deepcopy(self.tree)
        paths = {g["public_input_path"] for g in self.create()["groups"]}
        chosen = next(x for x in tree if x.get("path") in paths)
        tree.remove(chosen)
        with self.assertRaises(PilotMetadataError):
            self.create(tree=tree)

    def test_remote_duplicated_file_rejected(self):
        tree = copy.deepcopy(self.tree)
        entry = next(x for x in tree if x.get("type") == "file")
        tree.append(copy.deepcopy(entry))
        with self.assertRaises(PilotMetadataError):
            self.create(tree=tree)

    def test_task_file_tamper_rejected(self):
        with self.assertRaises(PilotMetadataError):
            self.create(tasks=self.tasks + b" ")

    def test_stratum_mismatch_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["tasks"][0]["operation"] = "delete"
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_pilot_unknown_extra_metadata_rejected(self):
        p = copy.deepcopy(self.pilot)
        p["tasks"][0]["ground_truth_ifc"] = "never publish"
        with self.assertRaises(PilotMetadataError):
            self.create(pilot=p)

    def test_remote_file_size_invalid_rejected(self):
        tree = copy.deepcopy(self.tree)
        groups = {g["public_input_path"] for g in self.create()["groups"]}
        for entry in tree:
            if entry.get("path") in groups:
                entry["size"] = -1
                break
        with self.assertRaises(PilotMetadataError):
            self.create(tree=tree)

    def test_duplicate_json_fields_rejected(self):
        with self.assertRaises(PilotMetadataError):
            _load_json_bytes(b'{"task_id":"a","task_id":"b"}')

    def test_nan_rejected(self):
        with self.assertRaises(PilotMetadataError):
            _load_json_bytes(b'{"size": NaN}')


if __name__ == "__main__":
    unittest.main()
