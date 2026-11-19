"""Read-only BIM-Edit original pilot cached INPUT hash verification regression."""
from __future__ import annotations

from hashlib import sha1, sha256
import json
import os
from pathlib import Path
from unittest.mock import patch
import re
import tempfile
import unittest

from tools.audit_bim_edit_pilot_cached_input_bytes import (
    CachedInputIdentityBlocked, MAX_SINGLE_IFC_BYTES,
    SOURCE_PATH_REPORT_SHA256, REVIEW_QUEUE_SHA256,
    run_cached_input_audit, verify_one_cached_input,
)


def _fixture(root: Path, content: bytes, *, lfs: bool = False):
    source = root / "simple" / "fixture.ifc"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(content)
    digest = sha256(content).hexdigest()
    oid = sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
    metadata = {"path": "simple/fixture.ifc", "size": len(content), "oid": oid}
    if lfs:
        metadata["lfs"] = {"oid": digest, "size": len(content)}
    return source, metadata, digest


class TestCachedPublicInputByteAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.report = run_cached_input_audit(cls.root)

    def test_original_cohort_is_unchanged(self):
        r = self.report
        self.assertEqual(r["original_pilot_tasks"], 36)
        self.assertEqual(r["distinct_pilot_source_paths"], 25)
        self.assertEqual(r["verified_local_input_files"], 20)
        self.assertEqual(r["verified_pilot_tasks_with_local_input"], 30)
        self.assertEqual(r["pilot_tasks_without_verified_local_input"], 6)
        self.assertEqual(r["missing_local_source_paths"], 5)

    def test_real_file_content_sha256_for_all_existing_sources(self):
        r = self.report
        self.assertEqual(r["verified_local_distinct_byte_sha256"], 20)
        self.assertEqual(r["local_source_hash_bytes_read_for_sha256"], 40744368)
        self.assertEqual(r["remote_reported_missing_source_bytes"], 736810930)
        self.assertEqual(r["exact_duplicate_byte_sha256_groups"], [])
        verified = [x for x in r["rows"] if x["byte_sha256_verified"]]
        self.assertEqual(len(verified), 20)
        for row in verified:
            self.assertRegex(row["byte_sha256_verified"], r"^[0-9a-f]{64}$")
            self.assertEqual(row["status"], "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED")

    def test_actual_publisher_identity_checks(self):
        r = self.report
        self.assertEqual(r["verification_method_counts"], {
            "publisher_git_blob_sha1_and_local_sha256": 19,
            "publisher_lfs_sha256_and_local_sha256": 1,
        })
        for row in r["rows"]:
            if row["status"] == "MISSING_LOCAL_PINNED_INPUT":
                self.assertIsNone(row["byte_sha256_verified"])
                self.assertIsNone(row["verification_method"])

    def test_all_failures_remain_in_denominator(self):
        self.assertEqual(sum(x["task_count"] for x in self.report["rows"]), 36)
        self.assertEqual(
            sum(x["task_count"] for x in self.report["rows"] if x["status"] != "PUBLISHER_OBJECT_AND_LOCAL_SHA256_VERIFIED"),
            6
        )

    def test_approval_not_forged_by_integrity_success(self):
        r = self.report
        self.assertEqual(r["independent_underlying_building_lineages_verified"], 0)
        self.assertEqual(r["rights_cleared_for_external_provider"], 0)
        self.assertFalse(r["model_launch_allowed"])
        self.assertFalse(r["original_task_reference_file_role_read"])
        self.assertFalse(r["source_IFC_geometry_native_parsed"])
        self.assertIn("NOT_SCIENTIFIC_LAUNCH", r["status"])

    def test_cross_task_reference_aliases_are_explicit_without_gt_file_access(self):
        alias = self.report["cross_task_reference_alias_audit"]
        self.assertEqual(alias["source_paths_also_reference_paths_for_other_tasks_full324"], 12)
        self.assertEqual(alias["pilot_task_rows_using_cross_task_reference_paths_full324"], 22)
        self.assertEqual(alias["source_paths_also_reference_paths_for_pilot_tasks"], 1)
        self.assertEqual(alias["pilot_task_rows_using_reference_paths_of_other_pilot_tasks"], 7)
        self.assertEqual(alias["same_task_source_equals_reference_path"], 0)
        self.assertEqual(
            self.report["verified_cached_inputs_that_are_reference_paths_for_some_other_task"], 9
        )
        self.assertEqual(
            sum(row["is_cross_task_reference_alias_in_original_324"] for row in self.report["rows"]), 12
        )

    def test_alias_flag_is_not_a_scorer_path_or_approval(self):
        for row in self.report["rows"]:
            self.assertEqual(type(row["is_cross_task_reference_alias_in_original_324"]), bool)
            self.assertFalse(row["per_file_legal_provider_transfer_approved"])
        self.assertFalse(self.report["original_task_reference_file_role_read"])
        self.assertEqual(self.report["rights_cleared_for_external_provider"], 0)

    def test_input_hash_report_contains_no_reference_or_private_target(self):
        report_json = json.dumps(self.report, ensure_ascii=False)
        for forbidden in ('"ground_truth_ifc"', '"private_gt"', '"target_guids"', '"prompt"', '"grader_script"', '"official_score"'):
            self.assertNotIn(forbidden, report_json)

    def test_frozen_source_reports_have_exact_hash(self):
        self.assertEqual(
            sha256((self.root / "reports/bim_edit_pilot_source_path_independence_20261119.json").read_bytes()).hexdigest(),
            SOURCE_PATH_REPORT_SHA256,
        )
        self.assertEqual(
            sha256((self.root / "reports/bim_edit_pilot_lineage_review_queue_20261119.json").read_bytes()).hexdigest(),
            REVIEW_QUEUE_SHA256,
        )

    def test_synthetic_git_object_and_sha256_positive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, digest = _fixture(root, b"original synthetic tiny data")
            result = verify_one_cached_input(root, "simple/fixture.ifc", metadata)
            self.assertEqual(result["byte_sha256_verified"], digest)
            self.assertEqual(result["verification_method"], "publisher_git_blob_sha1_and_local_sha256")

    def test_synthetic_lfs_sha256_positive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, digest = _fixture(root, b"harmless synthetic LFS", lfs=True)
            result = verify_one_cached_input(root, "simple/fixture.ifc", metadata)
            self.assertEqual(result["byte_sha256_verified"], digest)
            self.assertEqual(result["verification_method"], "publisher_lfs_sha256_and_local_sha256")

    def test_fake_git_blob_sha_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, _ = _fixture(root, b"fixture")
            metadata["oid"] = "f" * 40
            with self.assertRaises(CachedInputIdentityBlocked):
                verify_one_cached_input(root, "simple/fixture.ifc", metadata)

    def test_fake_lfs_sha_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, _ = _fixture(root, b"fixture", lfs=True)
            metadata["lfs"]["oid"] = "a" * 64
            with self.assertRaises(CachedInputIdentityBlocked):
                verify_one_cached_input(root, "simple/fixture.ifc", metadata)

    def test_cached_source_size_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, _ = _fixture(root, b"fixture")
            metadata["size"] = len(b"fixture") + 1
            with self.assertRaises(CachedInputIdentityBlocked):
                verify_one_cached_input(root, "simple/fixture.ifc", metadata)

    def test_missing_input_remains_explicit_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("simple").mkdir()
            result = verify_one_cached_input(
                root, "simple/missing.ifc", {"size": 8, "oid": "a" * 40}
            )
            self.assertEqual(result["status"], "MISSING_LOCAL_PINNED_INPUT")
            self.assertIsNone(result["byte_sha256_verified"])

    def test_input_path_traversal_and_gt_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("simple").mkdir()
            for name in ("../bad.ifc", "simple/../../secret.ifc", "reference/gt.ifc", "simple/foo.ifc/..", r"simple\bar.ifc"):
                with self.subTest(name=name), self.assertRaises(CachedInputIdentityBlocked):
                    verify_one_cached_input(root, name, {"size": 3, "oid": "a" * 40})

    def test_symlinked_cached_input_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("simple").mkdir()
            target = root / "other.ifc"
            target.write_bytes(b"fixture")
            try:
                os.symlink(target, root / "simple" / "fixture.ifc")
            except (OSError, NotImplementedError):
                self.skipTest("Windows symlink creation not permitted for test user")
            with self.assertRaises(CachedInputIdentityBlocked):
                verify_one_cached_input(root, "simple/fixture.ifc", {"size": 7, "oid": "a" * 40})

    def test_synthetic_size_limit_blocks_expensive_cached_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            f = root / "simple" / "huge.ifc"
            f.parent.mkdir()
            with f.open("wb") as stream:
                stream.truncate(MAX_SINGLE_IFC_BYTES + 1)  # sparse/no IFC generation
            result = verify_one_cached_input(
                root, "simple/huge.ifc", {"size": MAX_SINGLE_IFC_BYTES + 1, "oid": "a" * 40}
            )
            self.assertEqual(result["status"], "BLOCKED_PRESENT_EXCEEDS_PREAPPROVED_HASH_LIMIT")
            self.assertIsNone(result["byte_sha256_verified"])

    def test_original_publisher_croissant_license_is_only_dataset_level(self):
        snapshot = self.root / "reports/bim_edit_publisher_croissant_metadata_20261119.json"
        raw = snapshot.read_bytes()
        self.assertEqual(
            sha256(raw).hexdigest(),
            "aebfbcd3592ba57825e23e59c30ca2edca9b49e971338f54bf32fd233ef724a7"
        )
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(
            sha256(raw.replace(b"\n", b"\r\n")).hexdigest(),
            "04107063e34e0939eb1992e1830a4c9dc5ddd897060ad84c831a96f27ffae861"
        )
        metadata = json.loads(raw)
        self.assertEqual(metadata["name"], "BIMEdit")
        self.assertEqual(metadata["license"], "https://creativecommons.org/licenses/by/4.0/")
        recordset = next(row for row in metadata["recordSet"] if row.get("@id") == "ifc_models")
        exposed_fields = {field["@id"] for field in recordset["field"]}
        self.assertEqual(exposed_fields, {"file_path"})
        self.assertTrue(exposed_fields.isdisjoint({
            "creator", "copyright_holder", "source_project", "rightsholder",
            "license_per_file", "provider_transfer_permission", "retention_consent",
        }))
        self.assertEqual(self.report["rights_cleared_for_external_provider"], 0)

    def test_mocked_local_source_symlink_rejected_even_when_not_instantiable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, metadata, _ = _fixture(root, b"synthetic")
            original_is_symlink = Path.is_symlink
            with patch.object(
                Path, "is_symlink", autospec=True,
                side_effect=lambda path: path.name == "fixture.ifc" or original_is_symlink(path)
            ):
                with self.assertRaises(CachedInputIdentityBlocked):
                    verify_one_cached_input(root, "simple/fixture.ifc", metadata)

    def test_replay_frozen_new_report_exact(self):
        frozen = self.root / "reports/bim_edit_pilot_existing_cached_input_SHA256_20261119.json"
        if not frozen.exists():
            self.skipTest("Frozen new report generated after test-run bootstrapping")
        computed = (json.dumps(self.report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        self.assertEqual(frozen.read_bytes(), computed)


if __name__ == "__main__":
    unittest.main()
