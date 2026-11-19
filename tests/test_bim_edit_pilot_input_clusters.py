"""BIM-Edit primary pilot source-path metadata-only audit regression tests."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.audit_bim_edit_pilot_input_clusters import (
    PilotMetadataError, TASK_SHA256, _load_json_bytes,
    _path_only, build_pilot_source_path_audit, build_lineage_review_queue,
    run_audit, run_lineage_review,
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

    def review(self, *, baseline=None, tree=None, rights=None):
        if rights is None:
            rights = _load_json_bytes(
                (self.root / "manifests/source_rights.json").read_bytes()
            )
        return build_lineage_review_queue(
            self.create() if baseline is None else baseline,
            self.tree if tree is None else tree,
            rights,
        )

    def test_pilot_lineage_review_summary(self):
        r = self.review()
        self.assertEqual(r["exact_input_paths"], 25)
        self.assertEqual(r["distinct_public_git_sha1_oids"], 25)
        self.assertEqual(r["unverified_lfs_sha256_pointer_count"], 6)
        self.assertEqual(r["distinct_unverified_lfs_sha256_pointers"], 6)
        self.assertEqual(r["filename_clue_group_count_not_independent_sources"], 23)
        self.assertEqual(r["source_ifc_content_sha256_independently_verified"], 0)
        self.assertEqual(r["source_building_lineages_independently_verified"], 0)
        self.assertEqual(r["per_original_ifc_rights_verified"], 0)
        self.assertFalse(r["trial_launch_authorized"])
        self.assertEqual(len(r["review_queue"]), 25)
        self.assertEqual(len(r["filenames_suggesting_cross_path_lineage_review"]), 2)
        self.assertIn("BLOCKED", r["verdict"])

    def test_two_cross_path_stem_hints_are_not_rights_or_independence(self):
        r = self.review()
        families = {
            record["filename_stem_clue"]: record["public_input_paths_needing_independent_lineage_review"]
            for record in r["filenames_suggesting_cross_path_lineage_review"]
        }
        self.assertEqual(families["simple/task002"], [
            "simple/task002-create-input.ifc", "simple/task002-delete-input.ifc"
        ])
        self.assertEqual(families["simple/task007"], [
            "simple/task007-create-input.ifc", "simple/task007-update-input.ifc"
        ])
        for g in r["review_queue"]:
            self.assertIsNone(g["verified_original_ifc_sha256"])
            self.assertIsNone(g["verified_original_building_lineage"])
            self.assertFalse(g["per_file_rights_verified"])
            self.assertFalse(g["explicit_provider_transfer_retention_approved"])

    def test_review_queue_is_deterministic_without_ifc_open(self):
        original = run_lineage_review(self.root)
        again = run_lineage_review(self.root)
        self.assertEqual(original, again)
        self.assertEqual(
            len({row["public_input_path"] for row in original["review_queue"]}), 25
        )

    def test_original_frozen_report_sha_is_preserved(self):
        self.assertEqual(
            __import__("hashlib").sha256(
                (self.root / "reports/bim_edit_pilot_source_path_independence_20261119.json").read_bytes()
            ).hexdigest(),
            "6511d1f3783b9f031bd80060ce3e751730839683a9f2a7cc1ce2bd9f95ca9d01",
        )

    def test_forged_rights_flag_does_not_authorize_trial(self):
        rights = _load_json_bytes((self.root / "manifests/source_rights.json").read_bytes())
        for record in rights["records"]:
            if record["source"] == "BIM-Edit/BIM-Edit":
                record["rights_checked"] = True
        with self.assertRaises(PilotMetadataError):
            self.review(rights=rights)

    def test_unknown_asset_rights_record_rejected(self):
        rights = _load_json_bytes((self.root / "manifests/source_rights.json").read_bytes())
        rights["records"] = [record for record in rights["records"] if record["source"] != "BIM-Edit/BIM-Edit"]
        with self.assertRaises(PilotMetadataError):
            self.review(rights=rights)

    def test_remote_git_object_metadata_tamper_rejected(self):
        tree = copy.deepcopy(self.tree)
        paths = {g["public_input_path"] for g in self.create()["groups"]}
        for entry in tree:
            if entry.get("path") in paths:
                entry["oid"] = "invalid"
                break
        with self.assertRaises(PilotMetadataError):
            self.review(tree=tree)

    def test_remote_git_sha_duplicate_rejected(self):
        tree = copy.deepcopy(self.tree)
        paths = {g["public_input_path"] for g in self.create()["groups"]}
        entries = [row for row in tree if row.get("path") in paths]
        self.assertGreaterEqual(len(entries), 2)
        entries[1]["oid"] = entries[0]["oid"]
        with self.assertRaises(PilotMetadataError):
            self.review(tree=tree)

    def test_lfs_pointer_tamper_rejected(self):
        tree = copy.deepcopy(self.tree)
        paths = {g["public_input_path"] for g in self.create()["groups"]}
        for entry in tree:
            if entry.get("path") in paths and entry.get("lfs"):
                entry["lfs"]["oid"] = "a" * 64
                break
        with self.assertRaises(PilotMetadataError):
            self.review(tree=tree)

    def test_duplicate_source_group_and_wrong_status_rejected(self):
        baseline = self.create()
        baseline["groups"].append(copy.deepcopy(baseline["groups"][0]))
        with self.assertRaises(PilotMetadataError):
            self.review(baseline=baseline)
        baseline = self.create()
        baseline["status"] = "INDEPENDENTLY_CERTIFIED"
        with self.assertRaises(PilotMetadataError):
            self.review(baseline=baseline)

    def test_no_prompt_or_hidden_grading_information_leaks(self):
        r = self.review()
        content = json.dumps(r, ensure_ascii=False)
        for forbidden in ('"ground_truth_ifc"', '"target"', '"prompt"', '"secret"', '"private_gt"'):
            self.assertNotIn(forbidden, content)


if __name__ == "__main__":
    unittest.main()
